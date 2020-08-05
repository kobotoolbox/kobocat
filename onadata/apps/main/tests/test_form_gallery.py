import os

from onadata.apps.logger.models import XForm
from test_base import TestBase


class TestFormGallery(TestBase):

    def setUp(self):
        TestBase.setUp(self)
        self._create_user_and_login()
        self._publish_transportation_form()

    def test_cannot_publish_id_string_starting_with_number(self):
        xls_path = os.path.join(self.this_directory, "fixtures",
                                "transportation",
                                "transportation.id_starts_with_num.xls")
        count = XForm.objects.count()
        response = TestBase._publish_xls_file(self, xls_path)

        self.assertContains(response, 'Names must begin with a letter')
        self.assertEqual(XForm.objects.count(), count)
