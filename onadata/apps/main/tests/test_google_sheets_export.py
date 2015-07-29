import csv
import os

import gdata.gauth

from django.core.files.storage import get_storage_class
from django.core.files.temp import NamedTemporaryFile
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_datetime
from mock import Mock, patch

from onadata.apps.viewer.models.export import Export
from onadata.libs.utils.export_tools import generate_export
from onadata.libs.utils.google import oauth2_token
from onadata.libs.utils.google_sheets import SheetsClient
from test_base import TestBase


class TestExport(TestBase):

    def setUp(self):
        # Prepare a fake token.
        self.token = oauth2_token
        self.token.refresh_token = 'foo'
        self.token.access_token = 'bar'
        self.token_blob = gdata.gauth.token_to_blob(self.token)

        # Files that contain the expected spreadsheet data.
        self.fixture_dir = os.path.join(
            self.this_directory, 'fixtures', 'google_sheets_export')
        expected_file_names = ['expected_tutorial_w_repeats.csv',
                               'expected_children.csv']
        self.expected_files = [open(os.path.join(self.fixture_dir, f)) 
                               for f in expected_file_names]
        # Temporary files that receives spreadsheet data.
        self.result_files = [NamedTemporaryFile() for f in expected_file_names]
        self.csv_writers = [csv.writer(f, lineterminator='\n') 
                            for f in self.result_files]
        
        self._create_user_and_login()
        self._submission_time = parse_datetime('2013-02-18 15:54:01Z')

    def _mock_worksheet(self, csv_writer):
        """Creates a mock worksheet object with append_row and insert_row 
        methods writing to csv_writer."""
        worksheet = Mock()
        worksheet.append_row.side_effect = \
            lambda values: csv_writer.writerow(values) 
        worksheet.insert_row.side_effect = \
            lambda values, index: csv_writer.writerow(values) 
        return worksheet
        
    @patch.object(SheetsClient, 'new')
    @patch('urllib2.urlopen')
    def test_gsheets_export_output(self, mock_urlopen, mock_new):
        mock_urlopen.return_value.read.return_value = '{"access_token": "baz"}'
        mock_spreadsheet = Mock()
        mock_spreadsheet.add_worksheet.side_effect = \
            [self._mock_worksheet(writer) for writer in self.csv_writers]
        mock_new.return_value = mock_spreadsheet
        
        path = os.path.join(self.fixture_dir, 'tutorial_w_repeats.xls')
        self._publish_xls_file_and_set_xform(path)
        path = os.path.join(self.fixture_dir, 'tutorial_w_repeats.xml')
        self._make_submission(
            path, forced_submission_time=self._submission_time)
        # test csv
        export = generate_export(Export.GSHEETS_EXPORT, 'gsheets', 
                                 self.user.username, 'tutorial_w_repeats',
                                 google_token=self.token_blob)
        storage = get_storage_class()()
        self.assertTrue(storage.exists(export.filepath))
        path, ext = os.path.splitext(export.filename)
        self.assertEqual(ext, '.gsheets')

        for result, expected in zip(self.result_files, self.expected_files):
            result.flush()
            result.seek(0)
            expected_content = expected.read()
            result_content = result.read()
            self.assertEquals(result_content, expected_content)
                