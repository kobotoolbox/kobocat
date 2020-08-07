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


class UserProfileFormRegister(forms.Form):

    REGISTRATION_REQUIRE_CAPTCHA = settings.REGISTRATION_REQUIRE_CAPTCHA
    RECAPTCHA_PUBLIC_KEY = settings.RECAPTCHA_PUBLIC_KEY
    RECAPTCHA_HTML = captcha.displayhtml(settings.RECAPTCHA_PUBLIC_KEY,
                                         use_ssl=settings.RECAPTCHA_USE_SSL)

    name = forms.CharField(widget=forms.TextInput(), required=True,
                           max_length=255)
    city = forms.CharField(widget=forms.TextInput(), required=False,
                           max_length=255)
    country = forms.ChoiceField(widget=forms.Select(), required=False,
                                choices=COUNTRIES, initial='ZZ')
    organization = forms.CharField(widget=forms.TextInput(), required=False,
                                   max_length=255)
    home_page = forms.CharField(widget=forms.TextInput(), required=False,
                                max_length=255)
    twitter = forms.CharField(widget=forms.TextInput(), required=False,
                              max_length=255)

    recaptcha_challenge_field = forms.CharField(required=False, max_length=512)
    recaptcha_response_field = forms.CharField(
        max_length=100, required=settings.REGISTRATION_REQUIRE_CAPTCHA)

    def save(self, new_user):
        new_profile = \
            UserProfile(user=new_user, name=self.cleaned_data['name'],
                        city=self.cleaned_data['city'],
                        country=self.cleaned_data['country'],
                        organization=self.cleaned_data['organization'],
                        home_page=self.cleaned_data['home_page'],
                        twitter=self.cleaned_data['twitter'])
        new_profile.save()
        return new_profile


# order of inheritance control order of form display
class RegistrationFormUserProfile(RegistrationFormUniqueEmail,
                                  UserProfileFormRegister):

    class Meta:
        # JNM TEMPORARY
        model = User
        fields = ('username', 'email')

    # Those names conflicts with existing url patterns. Indeed, the root
    #  url pattern stating  states /<username> but you have /admin for
    # as admin url, /support as support url, etc. So you want to avoid
    # account created with those names.
    _reserved_usernames = [
        'accounts',
        'about',
        'admin',
        'clients',
        'data',
        'formhub',
        'forms',
        'maps',
        'odk',
        'ona',
        'people',
        'public',
        'submit',
        'submission',
        'support',
        'syntax',
        'xls2xform',
        'users',
        'worldbank',
        'unicef',
        'who',
        'wb',
        'wfp',
        'save',
        'ei',
        'modilabs',
        'mvp',
        'unido',
        'unesco',
        'savethechildren',
        'worldvision',
        'afsis'
    ]

    username = forms.CharField(widget=forms.TextInput(), max_length=30)
    email = forms.EmailField(widget=forms.TextInput())

    legal_usernames_re = re.compile("^\w+$")

    def clean(self):
        cleaned_data = super(UserProfileFormRegister, self).clean()

        # don't check captcha if it's disabled
        if not self.REGISTRATION_REQUIRE_CAPTCHA:
            if 'recaptcha_response_field' in self._errors:
                del self._errors['recaptcha_response_field']
            return cleaned_data

        response = captcha.submit(
            cleaned_data.get('recaptcha_challenge_field'),
            cleaned_data.get('recaptcha_response_field'),
            settings.RECAPTCHA_PRIVATE_KEY,
            None)

        if not response.is_valid:
            raise forms.ValidationError(_(u"The Captcha is invalid. "
                                          u"Please, try again."))
        return cleaned_data

    # This code use to be in clean_username. Now clean_username is just
    # a convenience proxy to this method. This method is here to allow
    # the UserProfileSerializer to validate the username without reinventing
    # the wheel while still avoiding the need to instancate the form. A even
    # cleaner way would be a shared custom validator.
    @classmethod
    def validate_username(cls, username):
        username = username.lower()
        if username in cls._reserved_usernames:
            raise forms.ValidationError(
                _(u'%s is a reserved name, please choose another') % username)
        elif not cls.legal_usernames_re.search(username):
            raise forms.ValidationError(
                _(u'username may only contain alpha-numeric characters and '
                  u'underscores'))
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_(u'%s already exists') % username)

    def clean_username(self):
        return self.validate_username(self.cleaned_data['username'])


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
