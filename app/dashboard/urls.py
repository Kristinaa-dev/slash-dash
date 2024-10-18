from django.urls import path
from . import views
from .views import docker_monitor_view, container_logs_view

urlpatterns = [
    path('', views.index, name='index'),
    path('system-data/', views.system_data, name='system_data'),
    path('docker/monitor/', docker_monitor_view, name='docker_monitor'),
    path('docker/<str:container_id>/logs/', container_logs_view, name='docker_logs'),
]

