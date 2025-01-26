from django.contrib import admin
from .models import Node, AlertRule, MetricType, TimeSeriesData, LogEntry

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'status', 'last_check_in')

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('node', 'metric_type', 'comparison_type', 'threshold', 'is_active')