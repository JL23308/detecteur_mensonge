from rest_framework import serializers
from api.models import Session, Device

class SessionSerializer(serializers.ModelSerializer):
    """
    Serializer for physiological interrogation sessions.
    The frontend sends `device_id` (integer PK); we map it to the `device` FK.
    """
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source='device',
        write_only=True,
        required=False,
        allow_null=True,
    )
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = ['id', 'device_id', 'device', 'calibration_base_bpm',
                  'start_time', 'end_time', 'is_active', 'duration']
        read_only_fields = ('user', 'start_time', 'is_active', 'device')

    def get_duration(self, obj):
        """Returns session duration in seconds, if ended."""
        if obj.end_time and obj.start_time:
            return (obj.end_time - obj.start_time).total_seconds()
        return None
