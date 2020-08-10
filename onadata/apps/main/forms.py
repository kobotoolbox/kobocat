import re
import urllib2
from urlparse import urlparse
from StringIO import StringIO

from django import forms
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from django.forms import ModelForm
from django.utils.translation import ugettext as _, ugettext_lazy
from django.conf import settings
from recaptcha.client import captcha
from registration.forms import RegistrationFormUniqueEmail
from registration.models import RegistrationProfile
from rest_framework.serializers import ValidationError

from pyxform.xls2json_backends import csv_to_dict

from onadata.apps.main.models import UserProfile
from onadata.apps.viewer.models.data_dictionary import upload_to
from onadata.libs.utils.country_field import COUNTRIES
from onadata.libs.utils.logger_tools import publish_xls_form


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        # Include only `require_auth` since others are now stored in KPI
        fields = ('require_auth',)


class MediaForm(forms.Form):
    media = forms.FileField(label=ugettext_lazy(u"Media upload"),
                            required=True)

    def clean_media(self):
        data_type = self.cleaned_data['media'].content_type
        if data_type not in ['image/jpeg', 'image/png', 'audio/mpeg']:
            raise forms.ValidationError('Only these media types are \
                                        allowed .png .jpg .mp3 .3gp .wav')


class QuickConverterForm(forms.Form):

    xls_file = forms.FileField(
        label=ugettext_lazy(u'XLS File'), required=True)

    def publish(self, user, id_string=None):
        if self.is_valid():
            cleaned_xls_file = self.cleaned_data['xls_file']

            # publish the xls
            return publish_xls_form(cleaned_xls_file, user, id_string)
