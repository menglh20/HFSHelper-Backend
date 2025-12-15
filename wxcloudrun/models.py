from datetime import datetime

from django.db import models


# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class Result(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.ForeignKey(User, on_delete=models.CASCADE)
    time = models.CharField(max_length=50)
    result = models.IntegerField()
    comment = models.IntegerField()
    detail = models.CharField(max_length=1000)
    save_path = models.CharField(max_length=1000)
    fileId = models.CharField(max_length=1000, default="")

    def __str__(self):
        return f"{self.name} - {self.result} at {self.time}"