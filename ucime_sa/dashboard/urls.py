from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('system-data/', views.system_data, name='system_data'),
]

