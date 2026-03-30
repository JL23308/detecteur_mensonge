from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import Device, Measure
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

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Custom endpoint for the M5StickC to get its current lie state.
        Usage: GET /api/devices/status/?mac=<mac_address>
        """
        mac = request.query_params.get('mac')
        if not mac:
            return Response({'error': 'Missing MAC parameter'}, status=400)
        
        # Get the most recent measure for this specific device MAC
        latest_measure = Measure.objects.filter(device_mac=mac).order_by('-timestamp').first()
        if not latest_measure:
            return Response({'is_lie': False, 'message': 'No measures found for this device'})
            
        return Response({'is_lie': latest_measure.is_lie})
