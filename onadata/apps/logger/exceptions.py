# coding: utf-8
from django.utils.translation import gettext as t


class DuplicateUUIDError(Exception):
    pass


class FormInactiveError(Exception):
    def __str__(self):
        return t("Form is inactive")
