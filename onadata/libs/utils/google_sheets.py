"""
This module contains classes responsible for communicating with
Google Data API and common spreadsheets models.
"""

class Client(object):

    """An instance of this class communicates with Google Data API."""
    
    def __init__(self, auth, http_session=None):
        pass

    def login(self):
        """Authorize client using ClientLogin protocol."""
        pass
    
    def new(self, title):
        pass
    
    def open(self, title):
        """Opens a spreadsheet."""
        pass

    def open_by_key(self, key):
        """Opens a spreadsheet specified by `key`."""
        pass
    
class Spreadsheet(object):

    """ A class for a spreadsheet object."""

    def __init__(self, client, feed_entry):
        pass

    def add_worksheet(self, title, rows, cols):
        pass

    def del_worksheet(self, worksheet):
        pass

    def worksheets(self):
        pass

    def worksheet(self, title):
        pass

    def get_worksheet(self, index):
        pass

    @property
    def title(self):
        pass

class Worksheet(object):

    """A class for worksheet object."""

    def __init__(self, spreadsheet, element):
        pass

    def cell(self, row, col):
        pass

    def row_values(self, row):
        pass

    def col_values(self, col):
        pass

    def update_cell(self, row, col, val):
        pass

    def resize(self, rows=None, cols=None):
        pass

    def add_rows(self, rows):
        pass

    def add_cols(self, cols):
        pass

    def append_row(self, values):
        pass

    def insert_row(self, values, index=1):
        pass


class Cell(object):

    def __init__(self, worksheet, element):
        pass
