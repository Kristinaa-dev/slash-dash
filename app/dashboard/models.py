# models.py
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.core.mail import send_mail
import sys
import requests

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
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='metrics')
    metric_type = models.ForeignKey(MetricType, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(db_index=True)
    value = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['node', 'timestamp']),
        ]           
        ordering = ['timestamp']


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

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    timestamp = models.DateTimeField(default=timezone.now)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    message = models.TextField()
    node = models.ForeignKey(Node, on_delete=models.CASCADE, null=True, blank=True)
    metric_type = models.ForeignKey(MetricType, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.severity}: {self.message[:50]}"

class AlertRule(models.Model):
    COMPARISON_CHOICES = [
        ('>', 'Greater than'),
        ('<', 'Less than'),
        ('>=', 'Greater or equal to'),
        ('<=', 'Less or equal to'),
        ('=', 'Equal to'),
        ('!=', 'Not equal to'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    node = models.ForeignKey(
        'Node',
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )
    metric_type = models.ForeignKey(
        'MetricType',
        on_delete=models.CASCADE,
        related_name='alert_rules'
    )

    threshold = models.FloatField()
    comparison_type = models.CharField(
        max_length=2,
        choices=COMPARISON_CHOICES,
        default='>'
    )
    
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='info'
    )
    
    # Cooldown to avoid spamming
    cooldown_minutes = models.PositiveIntegerField(default=0)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def trigger_alert(self, current_value):
        # This demonstration writes to a file for debugging; remove or adjust as needed.
        sys.stdout = open('debug.txt', 'w')
        print("ALERT RULES")
        print("ALERTTRIGGERED")
        
        
        
        # In AlertRule model's trigger_alert method - Add this before saving
        
        
        now = timezone.now()
        # Respect cooldown if defined
        if self.last_triggered_at and self.cooldown_minutes > 0:
            next_allowed_time = self.last_triggered_at + timezone.timedelta(minutes=self.cooldown_minutes)
            if now < next_allowed_time:
                return  # Still in cooldown period, skip
        
        # 1. Create log entry
        log_msg = (
            f"Alert triggered! Node='{self.node.name}', "
            f"Metric='{self.metric_type.name}', Value={current_value}, "
            f"Rule=({self.comparison_type} {self.threshold})."
        )
        Alert.objects.create(
            timestamp=now,
            severity=self.severity,
            message=log_msg,
            node=self.node,
            metric_type=self.metric_type
        )

        # Map severity to a LogEntry priority
        priority_map = {
            'info': 6,       # Info
            'warning': 4,    # Warning
            'critical': 2,   # Critical
        }
        chosen_priority = priority_map.get(self.severity, 6)  # default to info

        LogEntry.objects.create(
            timestamp=now,
            hostname=self.node.name,
            service="Alert Service",
            priority=chosen_priority,
            message=f"Alert triggered! Node='{self.node.name}',Metric='{self.metric_type.name}', Value={current_value}, Rule=({self.comparison_type} {self.threshold})."
        )

        # 2. Send an email
        subject = f"[ALERT] {self.metric_type.name} on {self.node.name}"
        email_body = (
            f"Dear {self.user.username},\n\n"
            f"{log_msg}\n\n"
            "Best regards,\n"
            "Your Monitoring System"
        )

        send_mail(
            subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
            # fail_silently=True
        )

        discord_webhook_url = "https://discord.com/api/webhooks/<URL>"

        if discord_webhook_url:
            # Customize your Discord message format as you like
            discord_message = (
                f"**Alert:**\n"
                f"- Node: {self.node.name}\n"       
                f"- Metric: {self.metric_type.name}\n"
                f"- Value: {current_value}\n"
                f"- Rule: {self.comparison_type} {self.threshold}\n\n"
                f"*Severity:* **{self.severity.upper()}**"
            )
            try:        
                requests.post(discord_webhook_url, json={"content": discord_message}, timeout=5)
            except requests.exceptions.RequestException as e:
                # Log error or handle exception as needed
                print(f"Failed to send Discord notification: {e}")

        self.last_triggered_at = now
        self.save()

    def __str__(self):
        return (
            f"AlertRule (User: {self.user}, Node: {self.node}, "
            f"Metric: {self.metric_type}, {self.comparison_type} {self.threshold})"
        )
