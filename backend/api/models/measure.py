from django.db import models
from .session import Session

class Measure(models.Model):
    """
    Model representing a single heartbeat reading and the lie diagnostic 
    sent by the device at a specific timestamp.
    """
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="measures", null=True, blank=True)
    device_mac = models.CharField(max_length=17, help_text="Logged MAC address at the time of measurement")
    bpm = models.FloatField(help_text="Current Beats Per Minute recorded by the device")
    base_bpm = models.FloatField(help_text="Baseline resting BPM used for calculation")
    is_lie = models.BooleanField(default=False, help_text="True if current BPM exceeds baseline by the threshold (e.g., > 20%)")
    shake_intensity = models.FloatField(default=0.0, help_text="Vibration intensity measured by accelerometer")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_measure"
        ordering = ['-timestamp']
        verbose_name = "Measure"
        verbose_name_plural = "Measures"

    def save(self, *args, **kwargs):
        # Business logic: a lie is detected if BPM > 20% of baseline
        if self.bpm and self.base_bpm:
            self.is_lie = self.bpm > (self.base_bpm * 1.20)
        super().save(*args, **kwargs)

    def __str__(self):
        status_text = "LIE DETECTED" if self.is_lie else "TRUTH"
        return f"Measure [{status_text}]: {self.bpm} BPM at {self.timestamp.strftime('%H:%M:%S')}"
