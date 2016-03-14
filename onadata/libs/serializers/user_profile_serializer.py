import copy
import six

from django.conf import settings
from django.forms import ValidationError as FormValidationError
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.validators import ValidationError
from registration.models import RegistrationProfile
from rest_framework import serializers

from onadata.apps.main.forms import UserProfileForm
from onadata.apps.main.forms import RegistrationFormUserProfile
from onadata.apps.main.models import UserProfile
from onadata.libs.serializers.fields.json_field import JsonField
from onadata.libs.permissions import CAN_VIEW_PROFILE, is_organization


def _get_first_last_names(name, limit=30):
    if not isinstance(name, six.string_types):
        return name, name

    if name.__len__() > (limit * 2):
        # since we are using the default django User Model, there is an
        # imposition of 30 characters on both first_name and last_name hence
        # ensure we only have 30 characters for either field

        return name[:limit], name[limit:limit * 2]

    name_split = name.split()
    first_name = name_split[0]
    last_name = u''

    if len(name_split) > 1:
        last_name = u' '.join(name_split[1:])

    return first_name, last_name


class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    is_org = serializers.SerializerMethodField('is_organization')
    username = serializers.CharField(source='user.username')

    # Added this field so it's required in the API in a clean way
    # and triggers validatino
    name = serializers.CharField(required=True)

    email = serializers.CharField(source='user.email')
    website = serializers.CharField(source='home_page', required=False)
    gravatar = serializers.ReadOnlyField()
    password = serializers.CharField(
        source='user.password', style={'input_type': 'password'}, required=False)
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)
    metadata = JsonField(required=False)
    id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = UserProfile

        fields = ('id', 'is_org', 'url', 'username', 'name', 'password',
                  'email', 'city', 'country', 'organization', 'website',
                  'twitter', 'gravatar', 'require_auth', 'user', 'metadata')
        extra_kwargs = {
            'url': {'lookup_field': 'user'}
        }

    def is_organization(self, obj):
        return is_organization(obj)

    def to_representation(self, obj):
        """
        Serialize objects -> primitives.
        """
        ret = super(UserProfileSerializer, self).to_representation(obj)
        if 'password' in ret:
            del ret['password']

        request = self.context['request'] \
            if 'request' in self.context else None

        if 'email' in ret and request is None or request.user \
                and not request.user.has_perm(CAN_VIEW_PROFILE, obj):
            del ret['email']

        return ret

    # Those 2 validations methods where embeded in the same code as
    # the create() method but DRF3 needs it to be separted now.
    # It uses to fill merge the form.errors and self._errors,
    # but you can't do it anymore so we validate the username, catch
    # the validation exception and reraise it in an exception DRF will
    # understand
    def validate_name(self, value):
        try:
            RegistrationFormUserProfile.validate_username(value)
        except FormValidationError as e:
            raise serializers.ValidationError(list(e))

        return value

    def validate_username(self, value):
        return self.validate_name(value)

    def create(self, validated_data):
        user = validated_data.get('user', {})
        username = user.get('username', None)
        password = user.get('password', None)
        email = user.get('email', None)

        site = Site.objects.get(pk=settings.SITE_ID)
        new_user = RegistrationProfile.objects.create_inactive_user(
            site,
            username=username,
            password=password,
            email=email,
            send_email=True)
        new_user.is_active = True
        new_user.save()

        created_by = self.context['request'].user
        created_by = None if created_by.is_anonymous() else created_by
        profile = UserProfile.objects.create(
            user=new_user, name=validated_data.get('name', u''),
            created_by=created_by,
            city=validated_data.get('city', u''),
            country=validated_data.get('country', u''),
            organization=validated_data.get('organization', u''),
            home_page=validated_data.get('home_page', u''),
            twitter=validated_data.get('twitter', u''))

        return profile

    def update(self, instance, validated_data):

        params = copy.deepcopy(validated_data)
        username = validated_data.get('user.username', None)
        password = validated_data.get('user.password', None)
        name = validated_data.get('name', None)
        email = validated_data.get('user.email', None)

        if username:
            params['username'] = username

        if email:
            params['email'] = email

        if password:
            params.update({'password1': password, 'password2': password})

            form = UserProfileForm(params, instance=instance)

            # form.is_valid affects instance object for partial updates [PATCH]
            # so only use it for full updates [PUT], i.e shallow copy effect
            if not self.partial and form.is_valid():
                instance = form.save()

            # get user
            if email:
                instance.user.email = form.cleaned_data['email']

            if name:
                first_name, last_name = _get_first_last_names(name)
                instance.user.first_name = first_name
                instance.user.last_name = last_name

            if email or name:
                instance.user.save()

        return super(UserProfileSerializer, self).update(instance, validated_data)


class UserProfileWithTokenSerializer(UserProfileSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')
    website = serializers.CharField(source='home_page', required=False)
    gravatar = serializers.ReadOnlyField()
    password = serializers.CharField(
        source='user.password', style={'input_type': 'password'}, required=False)
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)
    api_token = serializers.SerializerMethodField()
    temp_token = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('url', 'username', 'name', 'password', 'email', 'city',
                  'country', 'organization', 'website', 'twitter', 'gravatar',
                  'require_auth', 'user', 'api_token', 'temp_token')
        extra_kwargs = {
            "url": {'lookup_field': 'user'}
        }


    def get_api_token(self, object):
        return object.user.auth_token.key

    def get_temp_token(self, object):
        request = self.context['request']
        session_key = None
        if request:
            session = request.session
            session_key = session.session_key

        return session_key
