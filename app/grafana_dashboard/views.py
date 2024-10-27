from django.shortcuts import render

def index(request):
    return render(request, 'grafana_dashboard/index.html')
