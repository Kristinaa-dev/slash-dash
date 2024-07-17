from django.contrib import admin

# Register your models here.
from .models import Command

admin.site.register(Command)