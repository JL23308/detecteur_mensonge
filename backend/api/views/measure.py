from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from api.models import Device, Session, Measure
from api.serializers import MeasureSerializer
from django.shortcuts import get_object_or_404

class MeasureCreateView(APIView):
    """
    Endpoint for the IoT device (ESP32) to POST live measures.
    Uses Token auth — the same token defined in the Arduino sketch.
    Auto-creates the Device record on first contact so the dashboard
    shows it without any manual registration step.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print(f"\n[DEBUG] Incoming request from {request.META.get('REMOTE_ADDR')}")
        print(f"[DEBUG] Data: {request.data}")
        
        serializer = MeasureSerializer(data=request.data)
        if serializer.is_valid():
            mac = request.data.get('device_mac')
            print(f"[DEBUG] Valid data. MAC: {mac}")

            # Auto-create device for this user if it doesn't exist yet
            device, created = Device.objects.get_or_create(
                mac_address=mac,
                defaults={
                    'user': request.user,
                    'name': 'M5StickC Plus Unified',
                }
            )
            
            # If the device previously belonged to another user, transfer ownership dynamically
            if device.user != request.user:
                device.user = request.user
                device.save()

            # Link to the user's most recently created active session (allows multi-device sync)
            active_session = Session.objects.filter(user=request.user, is_active=True).order_by('-id').first()
            if active_session:
                print(f"[DEBUG] Linked to Session ID: {active_session.id}")
                serializer.save(session=active_session)
            else:
                print("[DEBUG] No active session found for user. Saving measure without session.")
                serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        print(f"[DEBUG] Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SessionMeasuresView(generics.ListAPIView):
    """
    Endpoint for the Frontend to retrieve all measures of a specific session.
    """
    serializer_class = MeasureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        session_id = self.kwargs['session_id']
        # Double check this session actually belongs to them (security)
        session = get_object_or_404(Session, id=session_id, user=self.request.user)
        return Measure.objects.filter(session=session).order_by('-timestamp')
