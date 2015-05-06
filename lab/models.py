from django.db import models


class Status(models.Model):
	key = models.CharField(max_length=32)
	value = models.CharField(max_length=255)
