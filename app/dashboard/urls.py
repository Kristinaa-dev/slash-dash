from django.urls import path
from . import views
from .views import docker_monitor

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # path('system-data/', views.system_data, name='system_data'),
    path('docker-monitor/', docker_monitor, name='docker_monitor'),
    path("terminal/", views.terminal_view, name="terminal"),
    # path('test', views.dashboard, name='dashboard'),
    path('latest-data/', views.latest_data, name='latest_data'),
    path('logs/', views.logs, name='logs'),
    
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
]

