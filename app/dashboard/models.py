from django.db import models

# Create your models here.
class Command(models.Model):
    command_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
class Creator(models.Model):
    command = models.ForeignKey(Command, on_delete=models.CASCADE)
    creator_name = models.CharField(max_length=200)
    admin = models.BooleanField(default=False)