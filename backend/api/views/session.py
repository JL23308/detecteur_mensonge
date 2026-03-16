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
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """
        Custom endpoint to mark a session as finished.
        """
        session = self.get_object()
        if not session.is_active:
            return Response({'status': 'Session already ended'}, status=400)
            
        session.is_active = false
        session.end_time = timezone.now()
        session.save()
        return Response({'status': 'Session ended successfully'})
