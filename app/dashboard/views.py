from django.shortcuts import render
from django.http import JsonResponse
import psutil
# Create your views here.

def get_system_data():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    
    return {
        'cpu_usage': cpu_usage,
        'memory_info': memory_info.total,
        'memory_used': memory_info.used,
        'memory_free': memory_info.free,
        'memory_percent': memory_info.percent,
        'disk_total': disk_info.total,
        'disk_used': disk_info.used,
        'disk_free': disk_info.free,
    }
    

def index(request):
    context = get_system_data()
    return render(request, 'dashboard/index.html', context)

def system_data(request):
    data = get_system_data()
    return JsonResponse(data)
    
