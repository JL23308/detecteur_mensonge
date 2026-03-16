from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from api.models import Device
from api.serializers import DeviceSerializer

class DeviceViewSet(viewsets.ModelViewSet):
    """
    CRUD Endpoint for managing devices linked to the authenticated user.
    """
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own attached devices
        return Device.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Automatically bounds the current authenticated user to the device
        serializer.save(user=self.request.user)
