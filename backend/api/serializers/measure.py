from rest_framework import serializers
from api.models import Measure

class MeasureSerializer(serializers.ModelSerializer):
    """
    Serializer for heart rate and lie detection points.
    The ESP32 only needs to send: device_mac, bpm, base_bpm, is_lie.
    session and timestamp are set server-side.
    """
    class Meta:
        model = Measure
        fields = ['id', 'session', 'device_mac', 'bpm', 'base_bpm', 'is_lie', 'shake_intensity', 'is_tremor_alert', 'timestamp']
        read_only_fields = ('id', 'session', 'is_lie', 'is_tremor_alert', 'timestamp')
