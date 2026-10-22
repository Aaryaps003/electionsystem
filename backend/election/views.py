import xml.etree.ElementTree as ET

from django.contrib.auth import authenticate
from django.core import signing
from django.db import transaction
from django.http import HttpResponse
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from . import services
from .models import Candidate, Voter
from .serializers import CandidateInputSerializer, VoterSerializer

VOTER_TOKEN_SALT = "election.voter-session"
VOTER_TOKEN_MAX_AGE = 30 * 60  # a voter session lasts 30 minutes


class LoginThrottle(AnonRateThrottle):
    """Slows down password guessing from a single IP address."""
    rate = "30/min"


# ---------- Voter session helpers ----------

def make_voter_token(voter):
    return signing.dumps({"vid": voter.pk}, salt=VOTER_TOKEN_SALT)


def voter_from_request(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        data = signing.loads(header[7:], salt=VOTER_TOKEN_SALT, max_age=VOTER_TOKEN_MAX_AGE)
    except signing.BadSignature:  # includes expired tokens
        return None
    return Voter.objects.filter(pk=data.get("vid")).first()


def voter_summary(v):
    return {"prn": v.prn, "name": v.name, "cls": v.cls, "division": v.division}


# ---------- Admin ----------

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def admin_login(request):
    user = authenticate(
        username=request.data.get("username", ""),
        password=request.data.get("password", ""),
    )
    if user is None or not user.is_staff:
        return Response({"error": "Invalid username or password."}, status=401)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_voters(request):
    return Response(VoterSerializer(Voter.objects.all(), many=True).data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def add_voter(request):
    ser = VoterSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    ser.save()
    services.broadcast_results()  # turnout denominator changed
    return Response(ser.data, status=201)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def reset_password(request):
    prn = str(request.data.get("prn", "")).strip()
    password = str(request.data.get("password", ""))
    if len(password) < 6:
        return Response({"error": "Password must be at least 6 characters."}, status=400)
    voter = Voter.objects.filter(prn=prn).first()
    if voter is None:
        return Response({"error": "Voter not found."}, status=404)
    voter.set_password(password)
    voter.save(update_fields=["password"])
    return Response({"message": "Password updated."})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def add_candidate(request):
    ser = CandidateInputSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=400)
    data = ser.validated_data
    with transaction.atomic():
        candidate = ser.save()
        # Every class/division gets a NOTA option automatically.
        Candidate.objects.get_or_create(
            prn=f"NOTA-{data['cls']}-{data['division']}",
            defaults={
                "name": "NOTA (None of the Above)",
                "cls": data["cls"],
                "division": data["division"],
                "is_nota": True,
            },
        )
    services.broadcast_results()
    return Response(services.candidate_dict(candidate), status=201)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def export_results(request):
    root = ET.Element("ElectionResults")
    stats = services.stats_payload()
    summary = ET.SubElement(root, "Summary")
    ET.SubElement(summary, "TotalVoters").text = str(stats["totalVoters"])
    ET.SubElement(summary, "VotesCast").text = str(stats["votesCast"])
    ET.SubElement(summary, "TurnoutPercent").text = str(stats["turnoutPercent"])

    cands = ET.SubElement(root, "Candidates")
    for c in services.results_payload():
        el = ET.SubElement(cands, "Candidate")
        for key in ("prn", "name", "cls", "division", "votes", "isNota"):
            ET.SubElement(el, key[0].upper() + key[1:]).text = str(c[key])

    xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    resp = HttpResponse(xml, content_type="application/xml")
    resp["Content-Disposition"] = 'attachment; filename="results.xml"'
    return resp


# ---------- Voter: login, ballot, vote ----------

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def voter_login(request):
    username = str(request.data.get("username", "")).strip().lower()
    password = str(request.data.get("password", ""))
    voter = Voter.objects.filter(username=username).first() if username else None
    # Same message for "no such user" and "wrong password" so usernames can't be probed.
    if voter is None or not voter.check_password(password):
        return Response({"error": "Incorrect username or password."}, status=401)
    if voter.has_voted:
        return Response({"error": "You have already voted. Each voter can vote only once."}, status=409)
    return Response({"token": make_voter_token(voter), "voter": voter_summary(voter)})


@api_view(["GET"])
def ballot(request):
    voter = voter_from_request(request)
    if voter is None:
        return Response({"error": "Your session has ended. Please sign in again."}, status=401)
    if voter.has_voted:
        return Response({"error": "You have already voted."}, status=409)
    candidates = Candidate.objects.filter(cls__iexact=voter.cls, division__iexact=voter.division)
    return Response({
        "voter": voter_summary(voter),
        "candidates": [services.candidate_dict(c) for c in candidates],
    })


@api_view(["POST"])
def cast_vote(request):
    # The voter comes from the signed session token, never from the request body,
    # so nobody can vote "as" someone else.
    session_voter = voter_from_request(request)
    if session_voter is None:
        return Response({"error": "Your session has ended. Please sign in again."}, status=401)

    candidate_prn = str(request.data.get("candidatePrn", "")).strip()
    with transaction.atomic():
        voter = Voter.objects.select_for_update().get(pk=session_voter.pk)
        if voter.has_voted:
            return Response({"error": "You have already voted."}, status=409)

        candidate = Candidate.objects.select_for_update().filter(prn=candidate_prn).first()
        if candidate is None:
            return Response({"error": "Candidate not found."}, status=404)
        if candidate.cls.lower() != voter.cls.lower() or candidate.division.lower() != voter.division.lower():
            return Response(
                {"error": "You can only vote for candidates in your own class and division."},
                status=403,
            )

        candidate.votes += 1
        candidate.save(update_fields=["votes"])
        voter.has_voted = True
        voter.save(update_fields=["has_voted"])

    services.broadcast_results()
    return Response({"message": "Vote recorded. Thank you!"})


# ---------- Results ----------

@api_view(["GET"])
def results(request):
    return Response(services.results_payload())


@api_view(["GET"])
def results_stats(request):
    return Response(services.stats_payload())
