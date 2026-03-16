from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from api.models import Device, Session, Measure
from api.serializers import MeasureSerializer
from django.shortcuts import get_object_or_404

class MeasureCreateView(APIView):
    """
    Endpoint specifically meant for the IoT Device (M5StickC) to POST live measures.
    We AllowAny since IoT devices lack proper JWT/Token auth mechanisms easily.
    """
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = MeasureSerializer(data=request.data)
        if serializer.is_valid():
            mac = request.data.get('device_mac')
            try:
                device = Device.objects.get(mac_address=mac)
                # Link to the device's currently active session if one exists
                active_session = Session.objects.filter(device=device, is_active=True).first()
                if active_session:
                    serializer.save(session=active_session)
                else:
                    serializer.save()
            except Device.DoesNotExist:
                # Still save the log even if device isn't registered on a user account yet
                serializer.save()
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
