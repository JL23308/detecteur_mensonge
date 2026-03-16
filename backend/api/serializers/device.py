from rest_framework import serializers
from api.models import Device

class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for the IoT Device model. 
    User and created_at fields are read-only to prevent tampering.
    """
    class Meta:
        model = Device
        fields = '__all__'
        read_only_fields = ('user', 'created_at')
