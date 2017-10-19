from django.conf import settings

SERVICE_CHOICES = [(u'f2dhis2', u'f2dhis2'), (u'generic_json', u'JSON POST'),
                   (u'generic_xml', u'XML POST'), (u'bamboo', u'bamboo')]

if settings.ENABLE_DESTRUCTIVE_REST_SERVICE:
    SERVICE_CHOICES.append((u'destructive_json', u'DESTRUCTIVE JSON POST'))
