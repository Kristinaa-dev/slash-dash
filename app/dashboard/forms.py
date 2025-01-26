from django import forms
from .models import Node

class NodeForm(forms.ModelForm):
    class Meta:
        model = Node
        fields = ['name', 'ip_address', 'node_type', 'location', 'ssh_username', 'ssh_password']

from .models import AlertRule

class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = ['node', 'metric_type', 'comparison_type', 'threshold', 'is_active']