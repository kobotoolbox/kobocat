from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.http.request import QueryDict

from rest_framework import filters
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import DjangoObjectPermissions

from onadata.libs.serializers.team_serializer import TeamSerializer
from onadata.apps.api.models import Team
from onadata.apps.api.tools import add_user_to_team, remove_user_from_team


class TeamViewSet(ModelViewSet):

    """
This endpoint allows you to create, update and view team information.

## GET List of Teams
Provides a json list of teams and the projects the team is assigned to.

<pre class="prettyprint">
<b>GET</b> /api/v1/teams
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/teams

> Response
>
>        [
>            {
>                "url": "https://example.com/api/v1/teams/1",
>                "name": "Owners",
>                "organization": "bruize",
>                "projects": []
>            },
>            {
>                "url": "https://example.com/api/v1/teams/2",
>                "name": "demo team",
>                "organization": "bruize",
>                "projects": []
>            }
>        ]

## GET Team Info for a specific team.

Shows teams details and the projects the team is assigned to, where:

* `pk` - unique identifier for the team

<pre class="prettyprint">
<b>GET</b> /api/v1/teams/<code>{pk}</code>
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/teams/1

> Response
>
>        {
>            "url": "https://example.com/api/v1/teams/1",
>            "name": "Owners",
>            "organization": "bruize",
>            "projects": []
>        }

## List members of a team

A list of usernames is the response for members of the team.

<pre class="prettyprint">
<b>GET</b> /api/v1/teams/<code>{pk}/members</code>
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/teams/1/members

> Response
>
>       ["member1"]
>

## Add a user to a team

POST `{"username": "someusername"}`
to `/api/v1/teams/<pk>/members` to add a user to
the specified team.
A list of usernames is the response for members of the team.

<pre class="prettyprint">
<b>POST</b> /api/v1/teams/<code>{pk}</code>/members
</pre>

> Response
>
>       ["someusername"]

"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    lookup_field = 'pk'
    extra_lookup_fields = None
    permission_classes = [DjangoObjectPermissions]
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    @detail_route(methods=['DELETE', 'GET', 'POST'])
    def members(self, request, *args, **kwargs):
        team = self.get_object()
        data = {}
        status_code = status.HTTP_200_OK

        if request.method in ['DELETE', 'POST']:
            username = request.data.get('username') or\
                request.query_params.get('username')

            if username:
                try:
                    user = User.objects.get(username__iexact=username)
                except User.DoesNotExist:
                    status_code = status.HTTP_400_BAD_REQUEST
                    data['username'] = [
                        _(u"User `%(username)s` does not exist."
                          % {'username': username})]
                else:
                    if request.method == 'POST':
                        add_user_to_team(team, user)
                    elif request.method == 'DELETE':
                        remove_user_from_team(team, user)
                    status_code = status.HTTP_201_CREATED
            else:
                status_code = status.HTTP_400_BAD_REQUEST
                data['username'] = [_(u"This field is required.")]

        if status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            data = [u.username for u in team.user_set.all()]

        return Response(data, status=status_code)
    
    @detail_route(methods=['DELETE', 'POST', 'GET'])
    def projects(self, request, *args, **kwargs):  # get, assign and dissociate projects from a team
        """
        # Get associated projects of a team
        <pre>GET https://www.example.com/api/v1/teams/1/projects</pre>
        Returns JSON Array of Assigned projects IDs
        # Associate a project to team
        <pre>POST https://www.example.com/api/v1/teams/1/projects</pre>
        <pre>POST Body
        {"project": 1}
        </pre>
        Response: Returns JSON Array of Assigned projects IDs
        # Dissociate a project from team
        <pre>DELETE https://www.example.com/api/v1/teams/1/projects</pre>
        <pre>DELETE Body
        [1,2,3,4]
        </pre>
        Response: Returns JSON Array of Assigned projects IDs
        """
        team = self.get_object()
        status_code = status.HTTP_200_OK
        request_data = request.data
        response_data = {}
        organization_projects = Project.objects.filter(organization=team.organization)
        if request_data and type(request_data) is QueryDict:
            project_id = request_data.get('project')
            try:
                project = Project.objects.get(id=project_id)
                if project in organization_projects:
                    if request.method == 'POST':
                        # assign project to team
                        team.projects.add(project)
                        status_code = status.HTTP_201_CREATED
                    elif request.method == 'DELETE':
                        # dissociate project from team
                        if project in team.projects.all():
                            team.projects.remove(project)
                            status_code = status.HTTP_201_CREATED

            except Project.DoesNotExist:
                status_code = status.HTTP_400_BAD_REQUEST
                return  Response({'project': [_(u"Project `%d` does not exist." % project_id)]}, status=status_code)

        # construct an array of team's projects IDs
        response_data = [p.id for p in team.projects.all()] if team.projects else []

        return Response(response_data, status=status_code)

