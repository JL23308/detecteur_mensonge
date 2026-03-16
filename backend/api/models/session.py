from django.db import models
from django.contrib.auth.models import User
from .device import Device

class Session(models.Model):
    """
    Model representing a lie-detector interrogation session. 
    It holds the calibration baseline BPM to compare against.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions", help_text="The user conducting the session")
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, related_name="sessions", help_text="Device used during this session")
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Whether this session is currently ongoing")
    calibration_base_bpm = models.FloatField(null=True, blank=True, help_text="The calibrated resting heart rate at the start")

    class Meta:
        db_table = "api_session"
        verbose_name = "Session"
        verbose_name_plural = "Sessions"

    def __str__(self):
        return f"Session {self.id} (User: {self.user.username})"
