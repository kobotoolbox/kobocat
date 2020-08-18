# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST


class NoConfirmationProvidedException(APIException):

    status_code = HTTP_400_BAD_REQUEST
    default_detail = _('No confirmation provided')
    default_code = 'no_confirmation_provided'
