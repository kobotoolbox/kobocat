# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import gettext as _


class DuplicateUUIDError(Exception):
    pass


@python_2_unicode_compatible
class FormInactiveError(Exception):
    def __str__(self):
        return _("Form is inactive")
