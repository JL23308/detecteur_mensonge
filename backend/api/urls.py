from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, DeviceViewSet, SessionViewSet, 
    MeasureCreateView, SessionMeasuresView
)

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('users/register/', RegisterView.as_view(), name='register'),
    path('users/login/', LoginView.as_view(), name='login'),
    path('measures/', MeasureCreateView.as_view(), name='create-measure'),
    path('sessions/<int:session_id>/measures/', SessionMeasuresView.as_view(), name='session-measures'),
    path('', include(router.urls)),
]
