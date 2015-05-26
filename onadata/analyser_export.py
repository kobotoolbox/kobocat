'''
Created on May 14, 2015

@author: esmail
'''


import zipfile

import lxml.etree as etree


NAMESPACES= {'ns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def update_shared_string_refs(worksheet, new_string_indices):
    raise NotImplementedError

def insert_shared_strings(source, destination, new_string_indices):
    original_string_indices= dict()
    destination_root= destination.getroot()
    for i, t_element in enumerate(destination_root.iterfind('.//ns:t', NAMESPACES)):
        original_string_indices[t_element.text]= i

    uniqueCount= i + 1
    for i, t_element in enumerate(source.iterfind('//ns:t', NAMESPACES)):
        text= t_element.text
        if text in original_string_indices:
            new_string_indices[i]= original_string_indices[text]
        else:
            # Copy the "si" element over.
            si_element= t_element.getparent()
            destination_root.append(si_element)
            new_string_indices[i]= uniqueCount
            uniqueCount+= 1


def insert_data_sheet(analyser_sheet, analyser_shared_strings, data_file_xlsx):
    with zipfile.ZipFile(data_file_xlsx) as data_zipfile:
        with data_zipfile.open('xl/sharedStrings.xml') as shared_strings_file:
            # FIXME: Not safe for multi-sheet data such for repeating groups.
            with data_zipfile.open('xl/worksheets/sheet1.xml') as data_sheet_file:
                data_shared_strings= etree.parse(shared_strings_file)
                new_string_indices= dict()
                insert_shared_strings(data_shared_strings, analyser_shared_strings, new_string_indices)

                data_sheet= etree.iterparse(data_sheet_file)
