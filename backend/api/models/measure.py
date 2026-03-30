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
    is_tremor_alert = models.BooleanField(default=False, help_text="True if vibrations exceed a threshold (e.g., > 0.5)")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_measure"
        ordering = ['-timestamp']
        verbose_name = "Measure"
        verbose_name_plural = "Measures"

    def save(self, *args, **kwargs):
        # Realistic Lie Detection Logic
        lie_score = 0
        if self.bpm and self.base_bpm:
            bpm_ratio = self.bpm / self.base_bpm
            if bpm_ratio > 1.10:
                # Add 1 point for every 1% above 110%
                lie_score += (bpm_ratio - 1.10) * 100
                
        if self.shake_intensity:
            if self.shake_intensity > 0.2:
                # Add points based on tremor intensity (e.g. 0.5 tremor -> 15 points)
                lie_score += self.shake_intensity * 30
            self.is_tremor_alert = self.shake_intensity > 0.5
            
        # Considered a lie if the combined score exceeds 15
        # This indicates either a large BPM spike, large tremors, or a combination of both
        self.is_lie = lie_score > 15
            
        super().save(*args, **kwargs)

    def __str__(self):
        status_text = "LIE DETECTED" if self.is_lie else "TRUTH"
        return f"Measure [{status_text}]: {self.bpm} BPM at {self.timestamp.strftime('%H:%M:%S')}"
