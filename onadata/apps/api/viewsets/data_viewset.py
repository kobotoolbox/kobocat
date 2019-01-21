import json
from xml.etree import ElementTree as et

from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import six
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied

from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ParseError
from rest_framework.settings import api_settings

from onadata.apps.api.viewsets.xform_viewset import custom_response_handler
from onadata.apps.api.tools import add_tags_to_instance, add_validation_status_to_instance, get_validation_status
from onadata.apps.logger.models.xform import XForm
from onadata.apps.logger.models.instance import Instance
from onadata.apps.viewer.models.parsed_instance import ParsedInstance
from onadata.libs.renderers import renderers
from onadata.libs.mixins.anonymous_user_public_forms_mixin import (
    AnonymousUserPublicFormsMixin)
from onadata.apps.api.permissions import XFormPermissions
from onadata.libs.serializers.data_serializer import (
    DataSerializer, DataListSerializer, DataInstanceSerializer)
from onadata.libs import filters
from onadata.libs.utils.viewer_tools import (
    EnketoError,
    get_enketo_edit_url)
from onadata.libs.utils.chart_tools import get_choice_label


SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


class DataViewSet(AnonymousUserPublicFormsMixin, ModelViewSet):

    """
This endpoint provides access to submitted data in JSON format. Where:

* `pk` - the form unique identifier
* `dataid` - submission data unique identifier
* `owner` - username of the owner(user/organization) of the data point

## GET JSON List of data end points

Lists the data endpoints accessible to requesting user, for anonymous access
a list of public data endpoints is returned.

<pre class="prettyprint">
<b>GET</b> /api/v1/data
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/data

> Response
>
>        [{
>            "id": 4240,
>            "id_string": "dhis2form"
>            "title": "dhis2form"
>            "description": "dhis2form"
>            "url": "https://example.com/api/v1/data/4240"
>         },
>            ...
>        ]

## Download data in `csv` format
<pre class="prettyprint">
<b>GET</b> /api/v1/data.csv</pre>
>
>       curl -O https://example.com/api/v1/data.csv

## GET JSON List of data end points filter by owner

Lists the data endpoints accessible to requesting user, for the specified
`owner` as a query parameter.

<pre class="prettyprint">
<b>GET</b> /api/v1/data?<code>owner</code>=<code>owner_username</code>
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/data?owner=ona

## Get Submitted data for a specific form
Provides a list of json submitted data for a specific form.
<pre class="prettyprint">
<b>GET</b> /api/v1/data/<code>{pk}</code></pre>
> Example
>
>       curl -X GET https://example.com/api/v1/data/22845

> Response
>
>        [
>            {
>                "_id": 4503,
>                "_bamboo_dataset_id": "",
>                "_deleted_at": null,
>                "expense_type": "service",
>                "_xform_id_string": "exp",
>                "_geolocation": [
>                    null,
>                    null
>                ],
>                "end": "2013-01-03T10:26:25.674+03",
>                "start": "2013-01-03T10:25:17.409+03",
>                "expense_date": "2011-12-23",
>                "_status": "submitted_via_web",
>                "today": "2013-01-03",
>                "_uuid": "2e599f6fe0de42d3a1417fb7d821c859",
>                "imei": "351746052013466",
>                "formhub/uuid": "46ea15e2b8134624a47e2c4b77eef0d4",
>                "kind": "monthly",
>                "_submission_time": "2013-01-03T02:27:19",
>                "required": "yes",
>                "_attachments": [],
>                "item": "Rent",
>                "amount": "35000.0",
>                "deviceid": "351746052013466",
>                "subscriberid": "639027...60317"
>            },
>            {
>                ....
>                "subscriberid": "639027...60317"
>            }
>        ]

## Get a single data submission for a given form

Get a single specific submission json data providing `pk`
 and `dataid` as url path parameters, where:

* `pk` - is the identifying number for a specific form
* `dataid` - is the unique id of the data, the value of `_id` or `_uuid`

<pre class="prettyprint">
<b>GET</b> /api/v1/data/<code>{pk}</code>/<code>{dataid}</code></pre>
> Example
>
>       curl -X GET https://example.com/api/v1/data/22845/4503

> Response
>
>            {
>                "_id": 4503,
>                "_bamboo_dataset_id": "",
>                "_deleted_at": null,
>                "expense_type": "service",
>                "_xform_id_string": "exp",
>                "_geolocation": [
>                    null,
>                    null
>                ],
>                "end": "2013-01-03T10:26:25.674+03",
>                "start": "2013-01-03T10:25:17.409+03",
>                "expense_date": "2011-12-23",
>                "_status": "submitted_via_web",
>                "today": "2013-01-03",
>                "_uuid": "2e599f6fe0de42d3a1417fb7d821c859",
>                "imei": "351746052013466",
>                "formhub/uuid": "46ea15e2b8134624a47e2c4b77eef0d4",
>                "kind": "monthly",
>                "_submission_time": "2013-01-03T02:27:19",
>                "required": "yes",
>                "_attachments": [],
>                "item": "Rent",
>                "amount": "35000.0",
>                "deviceid": "351746052013466",
>                "subscriberid": "639027...60317"
>            },
>            {
>                ....
>                "subscriberid": "639027...60317"
>            }
>        ]

Get a single specific submission json data providing `pk`
 and `dataid` as url path parameters with label fields, where:

* `pk` - is the identifying number for a specific form
* `dataid` - is the unique id of the data, the value of `_id` or `_uuid`
* ?label=true - parameter url allowing to replace "name" by "label" fields from the xform

<pre class="prettyprint">
<b>GET</b> /api/v1/data/<code>{pk}</code>/<code>{dataid}</code>?label=true</pre>
> Example
>
>       curl -X GET https://example.com/api/v1/data/22845/4503?label=true

> Response (ex: "name" = monthly, "label" = Monthly)
>
>            {
>                "_id": 4503,
>                "_bamboo_dataset_id": "",
>                "_deleted_at": null,
>                "expense_type": "service",
>                "_xform_id_string": "exp",
>                "_geolocation": [
>                    null,
>                    null
>                ],
>                "end": "2013-01-03T10:26:25.674+03",
>                "start": "2013-01-03T10:25:17.409+03",
>                "expense_date": "2011-12-23",
>                "_status": "submitted_via_web",
>                "today": "2013-01-03",
>                "_uuid": "2e599f6fe0de42d3a1417fb7d821c859",
>                "imei": "351746052013466",
>                "formhub/uuid": "46ea15e2b8134624a47e2c4b77eef0d4",
>                "kind": "Monthly",
>                "_submission_time": "2013-01-03T02:27:19",
>                "required": "yes",
>                "_attachments": [],
>                "item": "Rent",
>                "amount": "35000.0",
>                "deviceid": "351746052013466",
>                "subscriberid": "639027...60317"
>            },
>            {
>                ....
>                "subscriberid": "639027...60317"
>            }
>        ]

## Query submitted data of a specific form
Provides a list of json submitted data for a specific form. Use `query`
parameter to apply form data specific, see
<a href="http://docs.mongodb.org/manual/reference/operator/query/">
http://docs.mongodb.org/manual/reference/operator/query/</a>.

For more details see
<a href="https://github.com/modilabs/formhub/wiki/Formhub-Access-Points-(API)#
api-parameters">
API Parameters</a>.
<pre class="prettyprint">
<b>GET</b> /api/v1/data/<code>{pk}</code>?query={"field":"value"}</b>
<b>GET</b> /api/v1/data/<code>{pk}</code>?query={"field":{"op": "value"}}"</b>
</pre>
> Example
>
>       curl -X GET 'https://example.com/api/v1/data/22845?query={"kind": \
"monthly"}'
>       curl -X GET 'https://example.com/api/v1/data/22845?query={"date": \
{"gt$": "2014-09-29T01:02:03+0000"}}'

> Response
>
>        [
>            {
>                "_id": 4503,
>                "_bamboo_dataset_id": "",
>                "_deleted_at": null,
>                "expense_type": "service",
>                "_xform_id_string": "exp",
>                "_geolocation": [
>                    null,
>                    null
>                ],
>                "end": "2013-01-03T10:26:25.674+03",
>                "start": "2013-01-03T10:25:17.409+03",
>                "expense_date": "2011-12-23",
>                "_status": "submitted_via_web",
>                "today": "2013-01-03",
>                "_uuid": "2e599f6fe0de42d3a1417fb7d821c859",
>                "imei": "351746052013466",
>                "formhub/uuid": "46ea15e2b8134624a47e2c4b77eef0d4",
>                "kind": "monthly",
>                "_submission_time": "2013-01-03T02:27:19",
>                "required": "yes",
>                "_attachments": [],
>                "item": "Rent",
>                "amount": "35000.0",
>                "deviceid": "351746052013466",
>                "subscriberid": "639027...60317"
>            },
>            {
>                ....
>                "subscriberid": "639027...60317"
>            }
>        ]

## Query submitted data of a specific form using Tags
Provides a list of json submitted data for a specific form matching specific
tags. Use the `tags` query parameter to filter the list of forms, `tags`
should be a comma separated list of tags.

<pre class="prettyprint">
<b>GET</b> /api/v1/data?<code>tags</code>=<code>tag1,tag2</code></pre>
<pre class="prettyprint">
<b>GET</b> /api/v1/data/<code>{pk}</code>?<code>tags\
</code>=<code>tag1,tag2</code></pre>

> Example
>
>       curl -X GET https://example.com/api/v1/data/22845?tags=monthly

## Tag a submission data point

A `POST` payload of parameter `tags` with a comma separated list of tags.

Examples

- `animal fruit denim` - space delimited, no commas
- `animal, fruit denim` - comma delimited

<pre class="prettyprint">
<b>POST</b> /api/v1/data/<code>{pk}</code>/<code>{dataid}</code>/labels</pre>

Payload

    {"tags": "tag1, tag2"}

## Delete a specific tag from a submission

<pre class="prettyprint">
<b>DELETE</b> /api/v1/data/<code>{pk}</code>/<code>\
{dataid}</code>/labels/<code>tag_name</code></pre>

> Request
>
>       curl -X DELETE \
https://example.com/api/v1/data/28058/20/labels/tag1
or to delete the tag "hello world"
>
>       curl -X DELETE \
https://example.com/api/v1/data/28058/20/labels/hello%20world
>
> Response
>
>        HTTP 200 OK


## Query submitted validation status of a specific submission

<pre class="prettyprint">
<b>GET</b> /api/v1/data/<code>{pk}</code>/<code>{dataid}</code>/validation_status</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/data/22845/56/validation_status

> Response
>
>       {
>           "timestamp": 1513299978,
>           "by_whom ": "John Doe",
>           "uid": "validation_status_approved",
>           "color": "#00ff00",
>           "label: "Approved"
>       }

## Change validation status of a submission data point

A `PATCH` payload of parameter `validation_status`.

<pre class="prettyprint">
<b>PATCH</b> /api/v1/data/<code>{pk}</code>/<code>{dataid}</code>/validation_status</pre>

Payload

>       {
>           "validation_status_uid": "validation_status_not_approved"
>       }

> Example
>
>       curl -X PATCH https://example.com/api/v1/data/22845/56/validation_status

> Response
>
>       {
>           "timestamp": 1513299978,
>           "by_whom ": "John Doe",
>           "uid": "validation_status_not_approved",
>           "color": "#ff0000",
>           "label": "Not Approved"
>       }

## Get list of public data endpoints

<pre class="prettyprint">
<b>GET</b> /api/v1/data/public
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/data/public

> Response
>
>        [{
>            "id": 4240,
>            "id_string": "dhis2form"
>            "title": "dhis2form"
>            "description": "dhis2form"
>            "url": "https://example.com/api/v1/data/4240"
>         },
>            ...
>        ]

## Get enketo edit link for a submission instance

<pre class="prettyprint">
<b>GET</b> /api/v1/data/<code>{pk}</code>/<code>{dataid}</code>/enketo
</pre>

> Example
>
>       curl -X GET https://example.com/api/v1/data/28058/20/enketo?return_url=url

> Response
>       {"url": "https://hmh2a.enketo.formhub.org"}
>
>

## Delete a specific submission instance

Delete a specific submission in a form

<pre class="prettyprint">
<b>DELETE</b> /api/v1/data/<code>{pk}</code>/<code>{dataid}</code>
</pre>

> Example
>
>       curl -X DELETE https://example.com/api/v1/data/28058/20

> Response
>
>       HTTP 204 No Content
>
>
"""
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [
        renderers.XLSRenderer,
        renderers.XLSXRenderer,
        renderers.CSVRenderer,
        renderers.CSVZIPRenderer,
        renderers.SAVZIPRenderer,
        renderers.RawXMLRenderer
    ]

    content_negotiation_class = renderers.InstanceContentNegotiation
    filter_backends = (filters.AnonDjangoObjectPermissionFilter,
                       filters.XFormOwnerFilter)
    permission_classes = (XFormPermissions,)
    lookup_field = 'pk'
    lookup_fields = ('pk', 'dataid')
    extra_lookup_fields = None
    public_data_endpoint = 'public'

    queryset = XForm.objects.all()

    def get_serializer_class(self):
        pk_lookup, dataid_lookup = self.lookup_fields
        pk = self.kwargs.get(pk_lookup)
        dataid = self.kwargs.get(dataid_lookup)
        if pk is not None and dataid is None \
                and pk != self.public_data_endpoint:
            serializer_class = DataListSerializer
        elif pk is not None and dataid is not None:
            serializer_class = DataInstanceSerializer
        else:
            serializer_class = DataSerializer

        return serializer_class

    def get_object(self):
        obj = super(DataViewSet, self).get_object()
        pk_lookup, dataid_lookup = self.lookup_fields
        pk = self.kwargs.get(pk_lookup)
        dataid = self.kwargs.get(dataid_lookup)

        if pk is not None and dataid is not None:
            try:
                int(pk)
            except ValueError:
                raise ParseError(_(u"Invalid pk %(pk)s" % {'pk': pk}))
            try:
                int(dataid)
            except ValueError:
                raise ParseError(_(u"Invalid dataid %(dataid)s"
                                   % {'dataid': dataid}))

            obj = get_object_or_404(Instance, pk=dataid, xform__pk=pk)
            
            # Modify data object (label parameters)
            if self.request._request.GET.get('label') and self.request._request.GET.get('label').lower() == 'true':
                # Access to the right xform to get label
                xform = self._filtered_or_shared_qs(self.queryset, self.kwargs['pk'])[0]
                dd = xform.data_dictionary()
                tree = et.ElementTree(et.fromstring(obj.xml))
                # Parse the JSON object to replace "name" by "label" on JSON and XML part
                self.parseLabelJSON(obj.json, dd, tree)
                obj.xml = et.tostring(tree.getroot())

        return obj

    # Parsing JSON field and subfield to replace "name" by xform "label"
    def parseLabelJSON(self, JSONObj, xform_dict, tree):
        for item in JSONObj:
            # Key parsing
            real_item = item.split('/')[-1]
            # value is string/unicode ?
            if type(JSONObj[item]) is unicode:
                for ee in xform_dict.survey_elements:
                    if ee.label and ee.name == real_item and ee.children:
                        label = get_choice_label(ee.children, JSONObj[item])[0]
                        tree.find('.//' + item).text = label
                        JSONObj[item] = label
            elif type(JSONObj[item]) is list:
                tmp_dict = JSONObj[item]
                for index in tmp_dict:
                    self.parseLabelJSON(index, xform_dict, tree)

    def _get_public_forms_queryset(self):
        return XForm.objects.filter(Q(shared=True) | Q(shared_data=True))

    def _filtered_or_shared_qs(self, qs, pk):
        filter_kwargs = {self.lookup_field: pk}
        qs = qs.filter(**filter_kwargs)

        if not qs:
            filter_kwargs['shared_data'] = True
            qs = XForm.objects.filter(**filter_kwargs)

            if not qs:
                raise Http404(_(u"No data matches with given query."))

        return qs

    def filter_queryset(self, queryset, view=None):
        qs = super(DataViewSet, self).filter_queryset(queryset)
        pk = self.kwargs.get(self.lookup_field)
        tags = self.request.query_params.get('tags', None)

        if tags and isinstance(tags, six.string_types):
            tags = tags.split(',')
            qs = qs.filter(tags__name__in=tags).distinct()

        if pk:
            try:
                int(pk)
            except ValueError:
                if pk == self.public_data_endpoint:
                    qs = self._get_public_forms_queryset()
                else:
                    raise ParseError(_(u"Invalid pk %(pk)s" % {'pk': pk}))
            else:
                qs = self._filtered_or_shared_qs(qs, pk)

        return qs

    @detail_route(methods=["GET", "PATCH"])
    def validation_status(self, request, *args, **kwargs):
        """
        View or modify validation status of specific instance.
        User needs 'validate_xform' permission to update the data.

        :param request: Request
        :return: Response
        """
        http_status = status.HTTP_200_OK
        instance = self.get_object()
        data = {}

        if request.method == "PATCH":
            if request.user.has_perm("validate_xform", instance.asset):
                if not add_validation_status_to_instance(request, instance):
                    http_status = status.HTTP_400_BAD_REQUEST
            else:
                raise PermissionDenied(_(u"You do not have validate permissions."))

        if http_status == status.HTTP_200_OK:
            data = instance.validation_status

        return Response(data, status=http_status)

    @detail_route(methods=['GET', 'POST', 'DELETE'], extra_lookup_fields=['label', ])
    def labels(self, request, *args, **kwargs):
        http_status = status.HTTP_400_BAD_REQUEST
        instance = self.get_object()

        if request.method == 'POST':
            if add_tags_to_instance(request, instance):
                http_status = status.HTTP_201_CREATED

        tags = instance.tags
        label = kwargs.get('label', None)

        if request.method == 'GET' and label:
            data = [tag['name'] for tag in
                    tags.filter(name=label).values('name')]

        elif request.method == 'DELETE' and label:
            count = tags.count()
            tags.remove(label)

            # Accepted, label does not exist hence nothing removed
            http_status = status.HTTP_200_OK if count == tags.count() \
                else status.HTTP_404_NOT_FOUND

            data = list(tags.names())
        else:
            data = list(tags.names())

        if request.method == 'GET':
            http_status = status.HTTP_200_OK

        return Response(data, status=http_status)

    @detail_route(methods=['GET'])
    def enketo(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = {}
        if isinstance(self.object, XForm):
            raise ParseError(_(u"Data id not provided."))
        elif(isinstance(self.object, Instance)):
            if request.user.has_perm("change_xform", self.object.xform):
                return_url = request.query_params.get('return_url')
                if not return_url:
                    raise ParseError(_(u"return_url not provided."))

                try:
                    data["url"] = get_enketo_edit_url(
                        request, self.object, return_url)
                except EnketoError as e:
                    data['detail'] = "{}".format(e)
            else:
                raise PermissionDenied(_(u"You do not have edit permissions."))

        return Response(data=data)

    def retrieve(self, request, *args, **kwargs):
        # XML rendering does not a serializer
        if request.accepted_renderer.format == "xml":
            instance = self.get_object()
            return Response(instance.xml)
        else:
            # 14/01/2019 - GEOHYD/ANTEA : retrieve modify object (label parameters)
            #return super(DataViewSet, self).retrieve(request, *args, **kwargs)
            data = super(DataViewSet, self).retrieve(request, *args, **kwargs)
            instance = self.get_object()
            merged_obj = dict()
            merged_obj.update(data.data)
            merged_obj.update(instance.json)
            data.data = merged_obj
            return data

    def destroy(self, request, *args, **kwargs):
        self.object = self.get_object()

        if isinstance(self.object, XForm):
            raise ParseError(_(u"Data id not provided."))
        elif isinstance(self.object, Instance):

            if request.user.has_perm("delete_xform", self.object.xform):
                self.object.delete()
            else:
                raise PermissionDenied(_(u"You do not have delete "
                                         u"permissions."))

        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        lookup_field = self.lookup_field
        lookup = self.kwargs.get(lookup_field)

        if lookup_field not in kwargs.keys():
            self.object_list = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(self.object_list, many=True)

            return Response(serializer.data)

        if lookup == self.public_data_endpoint:
            self.object_list = self._get_public_forms_queryset()

            page = self.paginate_queryset(self.object_list)
            if page is not None:
                serializer = self.get_pagination_serializer(page)
            else:
                serializer = self.get_serializer(self.object_list, many=True)

            return Response(serializer.data)

        xform = self.get_object()
        query = request.GET.get("query", {})
        export_type = kwargs.get('format')
        if export_type is None or export_type in ['json']:
            # perform default viewset retrieve, no data export

            # With DRF ListSerializer are automatically created and wraps
            # everything in a list. Since this returns a list
            # # already, we unwrap it.
            res = super(DataViewSet, self).list(request, *args, **kwargs)
            res.data = res.data[0]
            return res

        return custom_response_handler(request, xform, query, export_type)

    def modify(self, request, *args, **kwargs):

        xform = self.get_object()
        http_status = status.HTTP_200_OK
        response = {}

        if request.user.has_perm("validate_xform", xform):

            owner = xform.user
            userform_id = "{}_{}".format(owner.username, xform.id_string)
            query = {ParsedInstance.USERFORM_ID: userform_id}  # Query used for MongoDB
            filter_ = {"xform_id": xform.id}  # Filter for Django ORM
            payload = {}

            try:
                payload = json.loads(request.data.get("payload", "{}"))
            except ValueError:
                http_status = status.HTTP_400_BAD_REQUEST
                response = {"detail": _("Invalid payload")}

            if http_status == status.HTTP_200_OK:

                new_validation_status_uid = payload.get("validation_status.uid")

                if new_validation_status_uid is None:
                    http_status = status.HTTP_400_BAD_REQUEST
                    response = {"detail": _("No validation_status.uid provided")}
                else:
                    # Create new validation_status object
                    new_validation_status = get_validation_status(
                        new_validation_status_uid, xform, request.user.username)

                    # 3 scenarios to update submissions

                    # First scenario / Modify submissions based on user's query
                    if payload.get("query"):
                        # Validate if query is valid.
                        try:
                            query.update(payload.get("query"))
                        except ValueError:
                            raise ParseError(_("Invalid query: %(query)s"
                                               % {'query': json.dumps(payload.get("query"))}))

                        query_kwargs = {
                            "query": json.dumps(query),
                            "fields": '["_id"]'
                        }

                        cursor = ParsedInstance.query_mongo_no_paging(**query_kwargs)
                        submissions_ids = [record.get("_id") for record in list(cursor)]
                        filter_.update({"id__in": submissions_ids})

                    # Second scenario / Modify submissions based on list of ids
                    elif payload.get("submissions_ids"):
                        try:
                            # Use int() to test if list of integers is valid.
                            submissions_ids = payload.get("submissions_ids", [])
                            or_ = {u"$or": [{u"_id": int(submission_id)} for submission_id in submissions_ids]}
                            query.update(or_)
                        except ValueError:
                            raise ParseError(_("Invalid submissions ids: %(submissions_ids)s"
                                               % {'submissions_ids': json.dumps(payload.get("submissions_ids"))}))

                        filter_.update({"id__in": submissions_ids})
                    # Third scenario / Modify all submissions in form, but confirmation param must be among payload
                    elif payload.get("confirm", False) is not True:
                        http_status = status.HTTP_400_BAD_REQUEST
                        response = {"detail": _("No confirmations provided")}

                    # If everything is OK, submit data to DBs
                    if http_status == status.HTTP_200_OK:
                        # Update Postgres & Mongo
                        updated_records_count = Instance.objects.\
                            filter(**filter_).update(validation_status=new_validation_status)
                        ParsedInstance.bulk_update_validation_statuses(query, new_validation_status)
                        response = {"detail": _("{} submissions have been updated").format(updated_records_count)}

            return Response(response, http_status)

        else:
            raise PermissionDenied(_(u"You do not have validate permissions."))
