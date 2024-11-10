# app/__init__.py
from .celery import celery_app

__all__ = ('celery_app',)
