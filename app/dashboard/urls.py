from django.urls import path
from . import views
from .views import docker_monitor

urlpatterns = [
    path('', views.index, name='index'),
    path('system-data/', views.system_data, name='system_data'),
    path('docker-monitor/', docker_monitor, name='docker_monitor'),

]

