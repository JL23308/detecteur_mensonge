from rest_framework import serializers
from api.models import Session

class SessionSerializer(serializers.ModelSerializer):
    """
    Serializer for physiological interrogation sessions.
    """
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = '__all__'
        read_only_fields = ('user', 'start_time')

    def get_duration(self, obj):
        """Returns session duration in seconds, if ended."""
        if obj.end_time and obj.start_time:
            return (obj.end_time - obj.start_time).total_seconds()
        return None
