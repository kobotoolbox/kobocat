from django.conf import settings
from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from onadata.libs.mixins.object_lookup_mixin import ObjectLookupMixin
from onadata.libs.serializers.user_profile_serializer import\
    UserProfileSerializer
from onadata.apps.main.models import UserProfile
from onadata.apps.api.permissions import UserProfilePermissions


class UserProfileViewSet(ObjectLookupMixin, ModelViewSet):
    """
List, Retrieve, Update, Create/Register users.

## Register a new User
<pre class="prettyprint"><b>POST</b> /api/v1/profiles</pre>
> Example
>
>        {
>            "username": "demo",
>            "name": "Demo User",
>            "email": "demo@localhost.com",
>            "city": "Kisumu",
>            "country": "KE",
>            ...
>        }

## List User Profiles
<pre class="prettyprint"><b>GET</b> /api/v1/profiles</pre>
> Example
>
>       curl -X GET https://example.com/api/v1/profiles

> Response
>
>       [
>        {
>            "url": "https://example.com/api/v1/profiles/demo",
>            "username": "demo",
>            "name": "Demo User",
>            "email": "demo@localhost.com",
>            "city": "",
>            "country": "",
>            "organization": "",
>            "website": "",
>            "twitter": "",
>            "gravatar": "https://secure.gravatar.com/avatar/xxxxxx",
>            "require_auth": false,
>            "user": "https://example.com/api/v1/users/demo"
>        },
>        {
>           ...}, ...
>       ]

## Retrieve User Profile Information

<pre class="prettyprint"><b>GET</b> /api/v1/profiles/{username}</pre>
<pre class="prettyprint"><b>GET</b> /api/v1/profiles/{pk}</pre>
> Example
>
>       curl -X GET https://example.com/api/v1/profiles/demo

> Response
>
>        {
>            "url": "https://example.com/api/v1/profiles/demo",
>            "username": "demo",
>            "name": "Demo User",
>            "email": "demo@localhost.com",
>            "city": "",
>            "country": "",
>            "organization": "",
>            "website": "",
>            "twitter": "",
>            "gravatar": "https://secure.gravatar.com/avatar/xxxxxx",
>            "require_auth": false,
>            "user": "https://example.com/api/v1/users/demo"

## Partial updates of User Profile Information

Properties of the UserProfile can be updated using `PATCH` http method.
Payload required is for properties that are to be changed in JSON,
for example, `{"country": "KE"}` will set the country to `KE`.

<pre class="prettyprint"><b>PATCH</b> /api/v1/profiles/{username}</pre>
> Example
>
>     \
curl -X PATCH -d '{"country": "KE"}' https://example.com/api/v1/profiles/demo \
-H "Content-Type: application/json"

> Response
>
>        {
>            "url": "https://example.com/api/v1/profiles/demo",
>            "username": "demo",
>            "name": "Demo User",
>            "email": "demo@localhost.com",
>            "city": "",
>            "country": "KE",
>            "organization": "",
>            "website": "",
>            "twitter": "",
>            "gravatar": "https://secure.gravatar.com/avatar/xxxxxx",
>            "require_auth": false,
>            "user": "https://example.com/api/v1/users/demo"
>        }

## Change authenticated user's password
> Example
>
>       curl -X POST -d current_password=password1 -d new_password=password2\
 https://example.com/api/v1/profile/demouser/change_password
> Response:
>
>        HTTP 200 OK
"""
    queryset = UserProfile.objects.exclude(user__pk=settings.ANONYMOUS_USER_ID)
    serializer_class = UserProfileSerializer
    permission_classes = [UserProfilePermissions]
    ordering = ('user__username', )

    # This is NOT DRF lookup_field. DRF lookup_field is only located on
    # seralizers and is deprecated and replaced by Meta.extra_kwargs['url']['lookup field']
    # This field is has been added by the previous dev, and is used to generate
    # a custom url routing on the fly. Basically it will be added in the
    # url regex.
    lookup_field = 'user'

    def get_object(self):
        """Lookup user profile by pk or username"""
        lookup = self.kwargs.get(self.lookup_field, None)
        if lookup is None:
            raise ParseError(
                'Expected URL keyword argument `%s`.' % self.lookup_field
            )
        queryset = self.filter_queryset(self.get_queryset())

        try:
            pk = int(lookup)
        except (TypeError, ValueError):
            filter_kwargs = {'username': lookup}
        else:
            filter_kwargs = {'pk': pk}

        # Return a 404 if the user does not exist
        user = get_object_or_404(User, **filter_kwargs)
        # Since the user does exist, create a matching profile if necessary
        obj, created = queryset.get_or_create(user=user)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    @detail_route(methods=['POST'])
    def change_password(self, request, *args, **kwargs):
        user_profile = self.get_object()
        current_password = request.data.get('current_password', None)
        new_password = request.data.get('new_password', None)

        if new_password:
            if user_profile.user.check_password(current_password):
                user_profile.user.set_password(new_password)
                user_profile.user.save()

                return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
