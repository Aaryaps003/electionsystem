
from rest_framework import serializers


class EligibilityAssignmentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField(min_value=1)