from django.db import models
from django.conf import settings

class Node(models.Model):
    NODE_TYPE_CHOICES = [
        ('Control', 'Control'),
        ('Agent', 'Agent'),
        ('Database', 'Database'),
    ]

    TYPE_LOCATION_CHOICES = [
        ('Europe', 'Europe'),
        ('US East', 'US East'),
        ('US West', 'US West'),
    ]

    name = models.CharField(max_length=100, help_text="A friendly name for the node")
    ip_address = models.GenericIPAddressField(help_text="The IP address (or domain) of the agent")
    node_type = models.CharField(max_length=50, choices=NODE_TYPE_CHOICES, help_text="Type of node")
    location = models.CharField(max_length=50, choices=TYPE_LOCATION_CHOICES, help_text="Node location")
    ssh_username = models.CharField(max_length=100, help_text="SSH username")
    ssh_password = models.CharField(max_length=100, help_text="SSH password")
    status = models.CharField(max_length=10, default='offline', help_text="online/offline")
    last_check_in = models.DateTimeField(null=True, blank=True, help_text="Last time the node responded")

    def __str__(self):
        return f"{self.name} ({self.ip_address})"








class MetricType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class TimeSeriesData(models.Model):
    """
    Stores the time series data for a given metric on a specific node.
    """
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='metrics')
    metric_type = models.ForeignKey(MetricType, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return f"{self.node.name} | {self.metric_type.name} at {self.timestamp}"


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
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=6)
    message = models.TextField()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.service}: {self.message[:50]}"
class AlertRule(models.Model):
    COMPARISON_CHOICES = [
        ('>', 'Greater than'),
        ('<', 'Less than'),
        ('>=', 'Greater or equal to'),
        ('<=', 'Less or equal to'),
        ('=', 'Equal to'),
        ('!=', 'Not equal to'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    node = models.ForeignKey(
        Node, 
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    metric_type = models.ForeignKey(
        MetricType,
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    threshold = models.FloatField()
    comparison_type = models.CharField(
        max_length=2,
        choices=COMPARISON_CHOICES,
        default='>'
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (f"AlertRule (User: {self.user.username}, Node: {self.node.name}, "
                f"Metric: {self.metric_type.name}, Threshold: {self.comparison_type} {self.threshold})")
    