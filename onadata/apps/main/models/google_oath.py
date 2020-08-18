# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.contrib.auth.models import User
from django.db import models


class TokenStorageModel(models.Model):
    id = models.OneToOneField(User, primary_key=True, related_name='google_id')
    token = models.TextField()

    class Meta:
        app_label = 'main'
