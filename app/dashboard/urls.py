from django.urls import path
from . import views
from .views import docker_monitor

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # path('system-data/', views.system_data, name='system_data'),
    path('docker-monitor/', views.docker_monitor, name='docker_monitor'),
    path('docker-action/<str:action>/<str:container_id>/', views.container_action, name='container_action'),
    path("terminal/", views.terminal_view, name="terminal"),
    # path('test', views.dashboard, name='dashboard'),
    path('latest-data/', views.latest_data, name='latest_data'),
    path('logs/', views.logs, name='logs'),
    
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    path('get-docker-stats/', views.get_docker_stats, name='get_docker_stats'),
    
    path("nodes/", views.node_list, name="node_list"),
    path("nodes/add", views.add_node, name="add_node"),
    
    path('get_node_data/', views.get_node_data, name='get_node_data'),
    
    # path('create-alert-rule/', views.create_alert_rule, name='create_alert_rule'),
    path('alerts/', views.alert_list, name='alert_list'),
    # path('alerts/ add', 
    
    path('log_priority_chart/', views.log_priority_chart, name='log_priority_chart'),
]

