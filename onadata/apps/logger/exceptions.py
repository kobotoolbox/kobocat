# -*- coding: utf-8 -*-

from django.utils.translation import gettext as _


class DuplicateUUIDError(Exception):
    pass


class FormInactiveError(Exception):
    def __unicode__(self):
        return _("Form is inactive")

    def __str__(self):
        return unicode(self).encode('utf-8')
