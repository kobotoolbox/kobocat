
from pybamboo.dataset import Dataset
from pybamboo.connection import Connection

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface
from onadata.apps.logger.models import XForm
from onadata.libs.utils.bamboo import get_new_bamboo_dataset, get_bamboo_url


class ServiceDefinition(RestServiceInterface):
    """
        @deprecated.
        This service should not be used anymore
    """

    id = u'bamboo'
    verbose_name = u'bamboo POST'

    def send(self, url, data):

        xform = XForm.objects.get(id=data.get("xform_id"))
        rows = [data.get("json")]

        # prefix meta columns names for bamboo
        prefix = (u'%(id_string)s_%(id)s'
                  % {'id_string': xform.id_string, 'id': xform.id})

        for row in rows:
            for col, value in row.items():
                if col.startswith('_') or col.startswith('meta_') \
                        or col.startswith('meta/'):
                    new_col = (u'%(prefix)s%(col)s'
                               % {'prefix': prefix, 'col': col})
                    row.update({new_col: value})
                    del(row[col])

        # create dataset on bamboo first (including current submission)
        if not xform.bamboo_dataset:
            dataset_id = get_new_bamboo_dataset(xform, force_last=True)
            xform.bamboo_dataset = dataset_id
            xform.save()
        else:
            dataset = Dataset(connection=Connection(url=get_bamboo_url(xform)),
                              dataset_id=xform.bamboo_dataset)
            dataset.update_data(rows=rows)
