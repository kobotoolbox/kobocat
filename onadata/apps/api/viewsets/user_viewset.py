from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.generics import get_object_or_404
from rest_framework.viewsets import ReadOnlyModelViewSet

from onadata.libs.serializers.user_serializer import UserSerializer
from onadata.apps.api import permissions


class UserViewSet(ReadOnlyModelViewSet):
    """
This endpoint allows you to list and retrieve user's first and last names.

## List Users
> Example
>
>       curl -X GET https://example.com/api/v1/users

> Response:

>       [
>            {
>                "username": "demo",
>                "first_name": "First",
>                "last_name": "Last"
>            },
>            {
>                "username": "another_demo",
>                "first_name": "Another",
>                "last_name": "Demo"
>            },
>            ...
>        ]


## Retrieve a specific user info

<pre class="prettyprint"><b>GET</b> /api/v1/users/{username}</pre>

> Example:
>
>        curl -X GET https://example.com/api/v1/users/demo

> Response:
>
>       {
>           "username": "demo",
>           "first_name": "First",
>           "last_name": "Last"
>       }

"""
    queryset = User.objects.exclude(pk=settings.ANONYMOUS_USER_ID)
    serializer_class = UserSerializer
    permission_classes = [permissions.ObjectPermissionsWithViewRestricted]

    # This is NOT DRF lookup_field. DRF lookup_field is only located on
    # seralizers and is deprecated and replaced by Meta.extra_kwargs['url']['lookup field']
    # This field is has been added by the previous dev, and is used to generate
    # a custom url routing on the fly. Basically it will be added in the
    # url regex.
    lookup_field = 'username'

    def get_object(self):
        """Lookup a  username by pk else use lookup_field"""
        queryset = self.filter_queryset(self.get_queryset())

        lookup = self.kwargs.get(self.lookup_field)
        filter_kwargs = {self.lookup_field: lookup}

        try:
            pk = int(lookup)
        except ValueError:
            pass
        else:
            filter_kwargs = {'pk': pk}

        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
