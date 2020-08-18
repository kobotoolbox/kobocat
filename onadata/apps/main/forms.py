# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import

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

from pyxform.xls2json_backends import csv_to_dict

from onadata.apps.main.models import UserProfile
from onadata.apps.viewer.models.data_dictionary import upload_to
from onadata.libs.utils.country_field import COUNTRIES
from onadata.libs.utils.logger_tools import publish_xls_form

FORM_LICENSES_CHOICES = (
    ('No License', ugettext_lazy('No License')),
    ('https://creativecommons.org/licenses/by/3.0/',
     ugettext_lazy('Attribution CC BY')),
    ('https://creativecommons.org/licenses/by-sa/3.0/',
     ugettext_lazy('Attribution-ShareAlike CC BY-SA')),
)

DATA_LICENSES_CHOICES = (
    ('No License', ugettext_lazy('No License')),
    ('http://opendatacommons.org/licenses/pddl/summary/',
     ugettext_lazy('PDDL')),
    ('http://opendatacommons.org/licenses/by/summary/',
     ugettext_lazy('ODC-BY')),
    ('http://opendatacommons.org/licenses/odbl/summary/',
     ugettext_lazy('ODBL')),
)

PERM_CHOICES = (
    ('view', ugettext_lazy('Can view')),
    ('edit', ugettext_lazy('Can edit')),
    ('report', ugettext_lazy('Can submit to')),
    ('validate', ugettext_lazy('Can validate')),
    ('remove', ugettext_lazy('Remove permissions')),
)


class DataLicenseForm(forms.Form):
    value = forms.ChoiceField(choices=DATA_LICENSES_CHOICES,
                              widget=forms.Select(
                                  attrs={'disabled': 'disabled',
                                         'id': 'data-license'}))


class FormLicenseForm(forms.Form):
    value = forms.ChoiceField(choices=FORM_LICENSES_CHOICES,
                              widget=forms.Select(
                                  attrs={'disabled': 'disabled',
                                         'id': 'form-license'}))


class PermissionForm(forms.Form):
    for_user = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'id': 'autocomplete',
                'data-provide': 'typeahead',
                'autocomplete': 'off'
            })
    )
    perm_type = forms.ChoiceField(choices=PERM_CHOICES, widget=forms.Select())

    def __init__(self, username):
        self.username = username
        super(PermissionForm, self).__init__()


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
            raise forms.ValidationError(_("The Captcha is invalid. "
                                          "Please, try again."))
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
                _('%s is a reserved name, please choose another') % username)
        elif not cls.legal_usernames_re.search(username):
            raise forms.ValidationError(
                _('username may only contain alpha-numeric characters and '
                  'underscores'))
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_('%s already exists') % username)

    def clean_username(self):
        return self.validate_username(self.cleaned_data['username'])


class SourceForm(forms.Form):
    source = forms.FileField(label=ugettext_lazy("Source document"),
                             required=True)


class SupportDocForm(forms.Form):
    doc = forms.FileField(label=ugettext_lazy("Supporting document"),
                          required=True)


class MediaForm(forms.Form):
    media = forms.FileField(label=ugettext_lazy("Media upload"),
                            required=True)

    def clean_media(self):
        data_type = self.cleaned_data['media'].content_type
        if data_type not in ['image/jpeg', 'image/png', 'audio/mpeg']:
            raise forms.ValidationError('Only these media types are \
                                        allowed .png .jpg .mp3 .3gp .wav')


class QuickConverterFile(forms.Form):
    xls_file = forms.FileField(
        label=ugettext_lazy('XLS File'), required=False)


class QuickConverterURL(forms.Form):
    xls_url = forms.URLField(label=ugettext_lazy('XLS URL'),
                             required=False)


class QuickConverterDropboxURL(forms.Form):
    dropbox_xls_url = forms.URLField(
        label=ugettext_lazy('XLS URL'), required=False)


class QuickConverterTextXlsForm(forms.Form):
    text_xls_form = forms.CharField(
        label=ugettext_lazy('XLSForm Representation'), required=False)


class QuickConverter(QuickConverterFile, QuickConverterURL,
                     QuickConverterDropboxURL, QuickConverterTextXlsForm):
    validate = URLValidator()

    def publish(self, user, id_string=None):
        if self.is_valid():
            # If a text (csv) representation of the xlsform is present,
            # this will save the file and pass it instead of the 'xls_file'
            # field.
            if 'text_xls_form' in self.cleaned_data\
               and self.cleaned_data['text_xls_form'].strip():
                csv_data = self.cleaned_data['text_xls_form']
                # "Note that any text-based field - such as CharField or
                # EmailField - always cleans the input into a Unicode string"
                # (https://docs.djangoproject.com/en/1.8/ref/forms/api/#django.forms.Form.cleaned_data).
                csv_data = csv_data.encode('utf-8')
                # requires that csv forms have a settings with an id_string or
                # form_id
                _sheets = csv_to_dict(StringIO(csv_data))
                try:
                    _settings = _sheets['settings'][0]
                    if 'id_string' in _settings:
                        _name = '%s.csv' % _settings['id_string']
                    else:
                        _name = '%s.csv' % _settings['form_id']
                except (KeyError, IndexError) as e:
                    raise ValueError('CSV XLSForms must have a settings sheet'
                                     ' and id_string or form_id')

                cleaned_xls_file = \
                    default_storage.save(
                        upload_to(None, _name, user.username),
                        ContentFile(csv_data))
            else:
                cleaned_xls_file = self.cleaned_data['xls_file']

            if not cleaned_xls_file:
                cleaned_url = self.cleaned_data['xls_url']
                if cleaned_url.strip() == '':
                    cleaned_url = self.cleaned_data['dropbox_xls_url']
                cleaned_xls_file = urlparse(cleaned_url)
                cleaned_xls_file = \
                    '_'.join(cleaned_xls_file.path.split('/')[-2:])
                if cleaned_xls_file[-4:] != '.xls':
                    cleaned_xls_file += '.xls'
                cleaned_xls_file = \
                    upload_to(None, cleaned_xls_file, user.username)
                self.validate(cleaned_url)
                xls_data = ContentFile(urllib2.urlopen(cleaned_url).read())
                cleaned_xls_file = \
                    default_storage.save(cleaned_xls_file, xls_data)
            # publish the xls
            return publish_xls_form(cleaned_xls_file, user, id_string)


class ActivateSMSSupportFom(forms.Form):

    enable_sms_support = forms.TypedChoiceField(coerce=lambda x: x == 'True',
                                                choices=((False, 'No'),
                                                         (True, 'Yes')),
                                                widget=forms.Select,
                                                label=ugettext_lazy(
                                                    "Enable SMS Support"))
    sms_id_string = forms.CharField(max_length=50, required=True,
                                    label=ugettext_lazy("SMS Keyword"))

    def clean_sms_id_string(self):
        sms_id_string = self.cleaned_data.get('sms_id_string', '').strip()

        if not re.match(r'^[a-z0-9\_\-]+$', sms_id_string):
            raise forms.ValidationError("id_string can only contain alphanum"
                                        " characters")

        return sms_id_string
