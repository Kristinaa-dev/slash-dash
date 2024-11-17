from django.db import models

class MetricType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class TimeSeriesData(models.Model):
    metric_type = models.ForeignKey(MetricType, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return f"{self.metric_type.name} at {self.timestamp}"

class LogEntry(models.Model):

    PRIORITY_CHOICES = [
        (7, 'Debug'),
        (6, 'Info'),
        (5, 'Notice'),
        (4, 'Warning'),
        (3, 'Error'),
        (2, 'Critical'),
        (1, 'Alert'),
        (0, 'Emergency'),
    ]
    

    timestamp = models.DateTimeField()
    hostname = models.CharField(max_length=255, null=True, blank=True)
    service = models.CharField(max_length=255)
    priority = models.IntegerField(choices=PRIORITY_CHOICES)
    message = models.TextField()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.service}: {self.message[:50]}"
#TODO: finish later consult with chatgpt have to rewrite the 
#      whole log collection and storage