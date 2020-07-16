# coding: utf-8
from django.contrib.auth.models import User
from django.db import models


class TokenStorageModel(models.Model):
    id = models.OneToOneField(User, primary_key=True, related_name='google_id', on_delete=models.CASCADE)
    token = models.TextField()

    class Meta:
        app_label = 'main'
