from django.db import models

class Notification(models.Model):
    receiver = models.CharField(max_length=255)
    cc = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Notification to {self.receiver}"

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
