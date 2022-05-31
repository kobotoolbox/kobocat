# coding: utf-8
from django.utils.translation import gettext_lazy as t
from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST


class NoConfirmationProvidedException(APIException):

    status_code = HTTP_400_BAD_REQUEST
    default_detail = t('No confirmation provided')
    default_code = 'no_confirmation_provided'
