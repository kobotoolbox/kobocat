from django.contrib.auth.models import User
from django.core.validators import ValidationError
from rest_framework import serializers

from onadata.apps.api import tools
from onadata.apps.api.models import OrganizationProfile
from onadata.apps.api.tools import get_organization_members
from onadata.apps.main.forms import RegistrationFormUserProfile
from onadata.libs.permissions import get_role_in_org


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    org = serializers.CharField(source='user.username', required=True)
    name = serializers.CharField(source='organization', required=True)
    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)
    creator = serializers.HyperlinkedRelatedField(
        view_name='user-detail', lookup_field='username', read_only=True)
    users = serializers.SerializerMethodField('get_org_permissions')


    # There is a bit of a mixup here, variables are called org, names
    # organization, org_name, username, etc.
    # Basically an organization is pair of User with a "username" and a
    # Organization with "name" that is the same as the user.username.
    # Organization si a subclass of UserProfile, and hence is attached to
    # the user.
    # An organization also has some kind of verbose name, which is
    # misleadingly stored in the atribute Organization.organization.

    # Curently the tests create an organization by sending :
    #        'org': u'someusername',
    #        'name': u'A verbose name',
    # with "org" being the username, and 'name' being the verbose name.

    class Meta:
        model = OrganizationProfile
        exclude = ('created_by', 'is_organization', 'organization')
        extra_kwargs = {
            'url': {'lookup_field': 'user'}
        }

    def create(self, validated_data):
        # get('user.username') does not work anymore:
        # username is in a nested dict
        org = validated_data.get('user', {}).get('username', None)
        creator = None

        if 'request' in self.context:
            creator = self.context['request'].user

        orgprofile = tools.create_organization_object(org, creator, validated_data)
        orgprofile.save()
        return orgprofile

    def validate_org(self, value):
        org = value.lower()
        if org in RegistrationFormUserProfile._reserved_usernames:
            raise ValidationError(
                u"%s is a reserved name, please choose another" % org)
        elif not RegistrationFormUserProfile.legal_usernames_re.search(org):
            raise ValidationError(
                u'organization may only contain alpha-numeric characters and '
                u'underscores')

        if User.objects.filter(username=org).exists():
            raise ValidationError(u'%s already exists' % org)

        return value

    def get_org_permissions(self, obj):
        members = get_organization_members(obj) if obj else []

        return [{
            'user': u.username,
            'role': get_role_in_org(u, obj)
        } for u in members]
