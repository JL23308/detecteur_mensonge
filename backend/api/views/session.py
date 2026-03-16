from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from api.models import Session
from api.serializers import SessionSerializer

class SessionViewSet(viewsets.ModelViewSet):
    """
    CRUD Endpoint for interrogation sessions.
    """
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Access is limited to sessions owned by the auth user
        return Session.objects.filter(user=self.request.user).order_by('-start_time')

    def perform_create(self, serializer):
        from django.utils import timezone
        from api.models import Device, Session as SessionModel

        # Retrieve the device from the validated data
        device = serializer.validated_data.get('device')

        # Close any existing active sessions for this device before starting a new one
        if device:
            SessionModel.objects.filter(device=device, is_active=True).update(
                is_active=False,
                end_time=timezone.now()
            )

        serializer.save(user=self.request.user)

        
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """
        Custom endpoint to mark a session as finished.
        """
        session = self.get_object()
        if not session.is_active:
            return Response({'status': 'Session already ended'}, status=400)
            
        session.is_active = False
        session.end_time = timezone.now()
        session.save()
        return Response({'status': 'Session ended successfully'})
