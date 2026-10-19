from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import StudentProfile

User = get_user_model()


class StudentManagementSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(
        source="student_profile.student_id",
        max_length=30,
    )
    department = serializers.CharField(
        source="student_profile.department",
        required=False,
        allow_blank=True,
    )
    year_of_study = serializers.IntegerField(
        source="student_profile.year_of_study",
        required=False,
        allow_null=True,
        min_value=1,
        max_value=10,
    )
    class_name = serializers.CharField(
        source="student_profile.class_name",
        max_length=100,
    )
    section = serializers.CharField(
        source="student_profile.section",
        max_length=20,
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "student_id",
            "department",
            "year_of_study",
            "class_name",
            "section",
            "password",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        value = value.strip().lower()
        queryset = User.objects.filter(email__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_username(self, value):
        value = value.strip()
        queryset = User.objects.filter(username__iexact=value)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "This username is already in use."
            )

        return value

    def validate(self, attrs):
        profile_data = attrs.get("student_profile", {})
        student_id = profile_data.get("student_id")

        queryset = StudentProfile.objects.all()

        if self.instance:
            queryset = queryset.exclude(user=self.instance)

        if student_id and queryset.filter(
            student_id=student_id
        ).exists():
            raise serializers.ValidationError({
                "student_id": "This student ID is already registered."
            })

        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({
                "password": "A password is required when creating a student."
            })

        if self.instance and "password" in attrs:
            attrs.pop("password", None)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_data = validated_data.pop("student_profile")
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.role = User.Role.VOTER
        user.set_password(password)
        user.save()

        StudentProfile.objects.create(
            user=user,
            **profile_data,
        )

        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("student_profile", {})
        validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        # Student management must never change account privileges.
        instance.role = User.Role.VOTER
        instance.save()

        profile, _ = StudentProfile.objects.get_or_create(
            user=instance,
            defaults={
                "student_id": profile_data.get("student_id", ""),
            },
        )

        for field, value in profile_data.items():
            setattr(profile, field, value)

        profile.save()

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["role"] = instance.role
        return data
