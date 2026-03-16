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
        serializer = MeasureSerializer(data=request.data)
        if serializer.is_valid():
            mac = request.data.get('device_mac')

            # Auto-create device for this user if it doesn't exist yet
            device, created = Device.objects.get_or_create(
                mac_address=mac,
                defaults={
                    'user': request.user,
                    'name': 'HUZZAH32 Detector',
                }
            )

            # Link to the device's most recently created active session
            active_session = Session.objects.filter(device=device, is_active=True).order_by('-id').first()
            if active_session:
                serializer.save(session=active_session)
            else:
                serializer.save()

            if created:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
