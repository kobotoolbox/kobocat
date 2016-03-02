import os

from datetime import datetime
import numpy as np
import inspect
import re

from django import forms
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db.models import Q
from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from taggit.forms import TagField
from rest_framework import exceptions
import rest_framework.views as rest_framework_views
from registration.models import RegistrationProfile

from onadata.apps.api.models.organization_profile import OrganizationProfile
from onadata.apps.api.models.project import Project
from onadata.apps.api.models.project_xform import ProjectXForm
from onadata.apps.api.models.team import Team
from onadata.apps.main.forms import QuickConverter
from onadata.apps.main.models import UserProfile
from onadata.apps.logger.models.xform import XForm
from onadata.apps.viewer.models.parsed_instance import datetime_from_str
from onadata.libs.data.query import get_field_records
from onadata.libs.data.query import get_numeric_fields
from onadata.libs.utils.logger_tools import publish_form
from onadata.libs.utils.logger_tools import response_with_mimetype_and_name
from onadata.libs.utils.user_auth import check_and_set_form_by_id
from onadata.libs.utils.user_auth import check_and_set_form_by_id_string
from onadata.libs.data.statistics import _chk_asarray
from onadata.libs.permissions import get_object_users_with_permissions,\
    get_role_in_org
from onadata.libs.permissions import OwnerRole, ReadOnlyRole
from onadata.libs.permissions import ROLES

DECIMAL_PRECISION = 2


def _get_first_last_names(name):
    name_split = name.split()
    first_name = name_split[0]
    last_name = u''
    if len(name_split) > 1:
        last_name = u' '.join(name_split[1:])
    return first_name, last_name


def _get_id_for_type(record, mongo_field):
    date_field = datetime_from_str(record[mongo_field])
    mongo_str = '$' + mongo_field

    return {"$substr": [mongo_str, 0, 10]} if isinstance(date_field, datetime)\
        else mongo_str


def get_accessible_forms(owner=None, shared_form=False, shared_data=False):
    xforms = XForm.objects.filter()

    if shared_form and not shared_data:
        xforms = xforms.filter(shared=True)
    elif (shared_form and shared_data) or \
            (owner == 'public' and not shared_form and not shared_data):
        xforms = xforms.filter(Q(shared=True) | Q(shared_data=True))
    elif not shared_form and shared_data:
        xforms = xforms.filter(shared_data=True)

    if owner != 'public':
        xforms = xforms.filter(user__username=owner)

    return xforms.distinct()


def create_organization(name, creator):
    """
    Organization created by a user
    - create a team, OwnerTeam with full permissions to the creator
        - Team(name='Owners', organization=organization).save()

    """
    organization = User.objects.create(username=name)
    organization_profile = OrganizationProfile.objects.create(
        user=organization, creator=creator)
    return organization_profile


def create_organization_object(org_name, creator, attrs={}):
    '''Creates an OrganizationProfile object without saving to the database'''
    name = attrs.get('name', org_name)
    first_name, last_name = _get_first_last_names(name)
    email = attrs.get('email', u'')
    new_user = User(username=org_name, first_name=first_name,
                    last_name=last_name, email=email, is_active=True)
    new_user.save()
    registration_profile = RegistrationProfile.objects.create_profile(new_user)
    if email:
        site = Site.objects.get(pk=settings.SITE_ID)
        registration_profile.send_activation_email(site)
    profile = OrganizationProfile(
        user=new_user, name=name, creator=creator,
        created_by=creator,
        city=attrs.get('city', u''),
        country=attrs.get('country', u''),
        organization=attrs.get('organization', u''),
        home_page=attrs.get('home_page', u''),
        twitter=attrs.get('twitter', u''))
    return profile


def create_organization_team(organization, name, permission_names=[]):
    organization = organization.user \
        if isinstance(organization, OrganizationProfile) else organization
    team = Team.objects.create(organization=organization, name=name)
    content_type = ContentType.objects.get(
        app_label='api', model='organizationprofile')
    if permission_names:
        # get permission objects
        perms = Permission.objects.filter(
            codename__in=permission_names, content_type=content_type)
        if perms:
            team.permissions.add(*tuple(perms))
    return team


def get_organization_members_team(organization):
    """Get organization members team
    create members team if it does not exist and add organization owner
    to the members team"""
    try:
        team = Team.objects.get(
            name=u'%s#%s' % (organization.user.username, 'members'))
    except Team.DoesNotExist:
        team = create_organization_team(organization, 'members')
        add_user_to_team(team, organization.user)

    return team


def remove_user_from_organization(organization, user):
    """Remove a user from an organization"""
    team = get_organization_members_team(organization)
    remove_user_from_team(team, user)


def remove_user_from_team(team, user):
    user.groups.remove(team)


def add_user_to_organization(organization, user):
    """Add a user to an organization"""
    team = get_organization_members_team(organization)
    add_user_to_team(team, user)


def add_user_to_team(team, user):
    user.groups.add(team)


def get_organization_members(organization):
    """Get members team user queryset"""
    team = get_organization_members_team(organization)

    return team.user_set.all()


def create_organization_project(organization, project_name, created_by):
    """Creates a project for a given organization
    :param organization: User organization
    :param project_name
    :param created_by: User with permissions to create projects within the
                       organization

    :returns: a Project instance
    """
    profile = OrganizationProfile.objects.get(user=organization)

    if not profile.is_organization_owner(created_by):
        return None

    project = Project.objects.create(name=project_name,
                                     organization=organization,
                                     created_by=created_by)

    return project


def add_team_to_project(team, project):
    """Adds a  team to a project

    :param team:
    :param project:

    :returns: True if successful or project has already been added to the team
    """
    if isinstance(team, Team) and isinstance(project, Project):
        if not team.projects.filter(pk=project.pk):
            team.projects.add(project)
        return True
    return False


def add_xform_to_project(xform, project, creator):
    """Adds an xform to a project"""
    # remove xform from any previous relation to a project
    xform.projectxform_set.all().delete()

    # make new connection
    instance = ProjectXForm.objects.create(
        xform=xform, project=project, created_by=creator)
    instance.save()

    # check if the project is a public and make the form public
    if project.shared != xform.shared:
        xform.shared = project.shared
        xform.shared_data = project.shared
        xform.save()

    for perm in get_object_users_with_permissions(project):
        user = perm['user']

        if user != creator:
            ReadOnlyRole.add(user, xform)
        else:
            OwnerRole.add(user, xform)

    return instance


def publish_xlsform(request, user, existing_xform=None):
    '''
    If `existing_xform` is specified, that form will be overwritten with the
    new XLSForm
    '''
    if not request.user.has_perm(
        'can_add_xform',
        UserProfile.objects.get_or_create(user=user)[0]
    ):
        raise exceptions.PermissionDenied(
            detail=_(u"User %(user)s has no permission to add xforms to "
                     "account %(account)s" % {'user': request.user.username,
                                              'account': user.username}))
    if existing_xform and not request.user.has_perm(
            'change_xform', existing_xform):
        raise exceptions.PermissionDenied(
            detail=_(u"User %(user)s has no permission to change this "
                     "form." % {'user': request.user.username, })
        )

    def set_form():
        form = QuickConverter(request.POST, request.FILES)
        if existing_xform:
            return form.publish(user, existing_xform.id_string)
        else:
            return form.publish(user)

    return publish_form(set_form)


def publish_project_xform(request, project):
    def set_form():
        form = QuickConverter(request.POST, request.FILES)

        return form.publish(project.organization)

    xform = None

    if 'formid' in request.data:
        xform = get_object_or_404(XForm, pk=request.data.get('formid'))
    else:
        xform = publish_form(set_form)

    if isinstance(xform, XForm):
        add_xform_to_project(xform, project, request.user)

    return xform


def mode(a, axis=0):
    """
    Adapted from
    https://github.com/scipy/scipy/blob/master/scipy/stats/stats.py#L568
    """
    a, axis = _chk_asarray(a, axis)
    scores = np.unique(np.ravel(a))       # get ALL unique values
    testshape = list(a.shape)
    testshape[axis] = 1
    oldmostfreq = np.zeros(testshape)
    oldcounts = np.zeros(testshape)
    for score in scores:
        template = (a == score)
        counts = np.expand_dims(np.sum(template, axis), axis)
        mostfrequent = np.where(counts > oldcounts, score, oldmostfreq)
        oldcounts = np.maximum(counts, oldcounts)
        oldmostfreq = mostfrequent
    return mostfrequent, oldcounts


def get_median_for_field(field, xform):
    return np.median(get_field_records(field, xform))


def get_median_for_numeric_fields_in_form(xform, field=None):
    data = {}
    for field_name in [field] if field else get_numeric_fields(xform):
        median = get_median_for_field(field_name, xform)
        data.update({field_name: median})
    return data


def get_mean_for_field(field, xform):
    return np.mean(get_field_records(field, xform))


def get_mean_for_numeric_fields_in_form(xform, field):
    data = {}
    for field_name in [field] if field else get_numeric_fields(xform):
        mean = get_mean_for_field(field_name, xform)
        data.update({field_name: round(mean, DECIMAL_PRECISION)})
    return data


def get_mode_for_field(field, xform):
    a = np.array(get_field_records(field, xform))
    m, count = mode(a)
    return m


def get_mode_for_numeric_fields_in_form(xform, field=None):
    data = {}
    for field_name in [field] if field else get_numeric_fields(xform):
        mode = get_mode_for_field(field_name, xform)
        data.update({field_name: round(mode, DECIMAL_PRECISION)})
    return data


def get_min_max_range_for_field(field, xform):
    a = np.array(get_field_records(field, xform))
    _max = np.max(a)
    _min = np.min(a)
    _range = _max - _min
    return _min, _max, _range


def get_min_max_range(xform, field=None):
    data = {}
    for field_name in [field] if field else get_numeric_fields(xform):
        _min, _max, _range = get_min_max_range_for_field(field_name, xform)
        data[field_name] = {'max': _max, 'min': _min, 'range': _range}
    return data


def get_all_stats(xform, field=None):
    data = {}
    for field_name in [field] if field else get_numeric_fields(xform):
        _min, _max, _range = get_min_max_range_for_field(field_name, xform)
        mode = get_mode_for_field(field_name, xform)
        mean = get_mean_for_field(field_name, xform)
        median = get_median_for_field(field_name, xform)
        data[field_name] = {
            'mean': round(mean, DECIMAL_PRECISION),
            'median': median,
            'mode': round(mode, DECIMAL_PRECISION),
            'max': _max,
            'min': _min,
            'range': _range
        }
    return data


def get_xform(formid, request, username=None):
    try:
        formid = int(formid)
    except ValueError:
        username = username is None and request.user.username
        xform = check_and_set_form_by_id_string(username, formid, request)
    else:
        xform = check_and_set_form_by_id(int(formid), request)

    if not xform:
        raise exceptions.PermissionDenied(_(
            "You do not have permission to view data from this form."))

    return xform


def get_user_profile_or_none(username):
    profile = None

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        pass
    else:
        profile, created = UserProfile.objects.get_or_create(user=user)

    return profile


def add_tags_to_instance(request, instance):
    class TagForm(forms.Form):
        tags = TagField()

    form = TagForm(request.data)

    if form.is_valid():
        tags = form.cleaned_data.get('tags', None)

        if tags:
            for tag in tags:
                instance.instance.tags.add(tag)
            instance.save()


def get_media_file_response(metadata):
    if metadata.data_file:
        file_path = metadata.data_file.name
        filename, extension = os.path.splitext(file_path.split('/')[-1])
        extension = extension.strip('.')
        dfs = get_storage_class()()

        if dfs.exists(file_path):
            response = response_with_mimetype_and_name(
                metadata.data_file_type,
                filename, extension=extension, show_date=False,
                file_path=file_path, full_mime=True)

            return response
        else:
            return HttpResponseNotFound()
    else:
        return HttpResponseRedirect(metadata.data_value)


def check_inherit_permission_from_project(xform_id, user):
    if xform_id == 'public':
        return

    try:
        int(xform_id)
    except ValueError:
        return

    # get the project_xform
    projects_xform = ProjectXForm.objects.filter(xform=xform_id)

    if not projects_xform:
        return

    # get and compare the project role to the xform role
    project_role = get_role_in_org(user, projects_xform[0].project)
    xform_role = get_role_in_org(user, projects_xform[0].xform)

    # if diff set the project role to the xform
    if xform_role != project_role:
        _set_xform_permission(project_role, user, projects_xform[0].xform)


def _set_xform_permission(role, user, xform):
    role_class = ROLES.get(role)

    if role_class:
        role_class.add(user, xform)

def get_view_name(view_cls, suffix=None):
    ''' Override Django REST framework's name for the base API class '''
    # The base API class should inherit directly from APIView. We can't use
    # issubclass() because ViewSets also inherit (indirectly) from APIView.
    try:
        if inspect.getmro(view_cls)[1] is rest_framework_views.APIView:
            return 'KoBo Api' # awkward capitalization for consistency
    except KeyError:
        pass
    return rest_framework_views.get_view_name(view_cls, suffix)

def get_view_description(view_cls, html=False):
    ''' Replace example.com in Django REST framework's default API description
    with the domain name of the current site '''
    domain = Site.objects.get_current().domain
    description = rest_framework_views.get_view_description(view_cls,
        html)
    # description might not be a plain string: e.g. it could be a SafeText
    # to prevent further HTML escaping
    original_type = type(description)
    description = original_type(re.sub(
        '(https*)://example.com',
        '\\1://{}'.format(domain),
        description
    ))
    return description
