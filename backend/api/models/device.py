from django.db import models
from django.contrib.auth.models import User

class Device(models.Model):
    """
    Model representing an IoT device (e.g., M5StickC) registered by a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices", help_text="The owner of the device")
    mac_address = models.CharField(max_length=17, unique=True, help_text="MAC Address of the ESP32 (e.g., 00:1A:2B:3C:4D:5E)")
    name = models.CharField(max_length=100, default="M5StickC Detector", help_text="Human-readable name for the device")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_device"
        verbose_name = "Device"
        verbose_name_plural = "Devices"

    def __str__(self):
        return f"{self.name} ({self.mac_address})"
