# dashboard/signals.py
import sys
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TimeSeriesData, AlertRule, LogEntry
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

def compare(value, threshold, comparison_type):
    if comparison_type == '>':
        return value > threshold
    elif comparison_type == '<':
        return value < threshold
    elif comparison_type == '>=':
        return value >= threshold
    elif comparison_type == '<=':
        return value <= threshold
    elif comparison_type == '=':
        return value == threshold
    elif comparison_type == '!=':
        return value != threshold
    return False


@receiver(post_save, sender=TimeSeriesData)
def check_alerts_on_new_timeseriesdata(sender, instance, created, **kwargs):
    """Checks and triggers alerts when a new TimeSeriesData is created."""
    if not created:
        return

    # print(f"Received post_save signal for TimeSeriesData ID: {instance.id}")

    # Fetch relevant AlertRules
    relevant_rules = AlertRule.objects.filter(
        node=instance.node,
        metric_type=instance.metric_type,
        is_active=True
    ).select_related('node', 'metric_type', 'user')

    # print(f"Found {relevant_rules.count()} relevant AlertRules for TimeSeriesData ID: {instance.id}")

    for rule in relevant_rules:
        if compare(instance.value, rule.threshold, rule.comparison_type):
            # print(f"AlertRule ID {rule.id} triggered by TimeSeriesData ID {instance.id}")
            rule.trigger_alert(current_value=instance.value)
        else:
            # print(f"AlertRule ID {rule.id} not triggered by TimeSeriesData ID {instance.id}")
            pass