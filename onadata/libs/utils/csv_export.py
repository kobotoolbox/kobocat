import csv

from django.core.files.temp import NamedTemporaryFile

from onadata.libs.utils.common_tags import INDEX, PARENT_INDEX
from onadata.libs.utils.export_builder import ExportBuilder


class FlatCsvExportBuilder(ExportBuilder):
    
    def export(self, path, data, username, id_string, filter_query):
        # TODO resolve circular import
        from onadata.apps.viewer.pandas_mongo_bridge import CSVDataFrameBuilder

        csv_builder = CSVDataFrameBuilder(
            username, id_string, filter_query, self.GROUP_DELIMITER,
            self.SPLIT_SELECT_MULTIPLES, self.BINARY_SELECT_MULTIPLES)
        csv_builder.export_to(path)
        
        
class ZippedCsvExportBuilder(ExportBuilder):
    
    @classmethod
    def write_row(row, csv_writer, fields):
        csv_writer.writerow(
            [ExportBuilder.encode_if_str(row, field) for field in fields])
            
    def export(self, path, data, *args):
        csv_defs = {}
        for section in self.sections:
            csv_file = NamedTemporaryFile(suffix=".csv")
            csv_writer = csv.writer(csv_file)
            csv_defs[section['name']] = {
                'csv_file': csv_file, 'csv_writer': csv_writer}

        # write headers
        for section in self.sections:
            fields = ([element['title'] for element in section['elements']] + 
                      self.EXTRA_FIELDS)
            csv_defs[section['name']]['csv_writer'].writerow(
                [f.encode('utf-8') for f in fields])

        indices = {}
        survey_name = self.survey.name
        for index, d in enumerate(data, 1):
            # decode mongo section names
            joined_export = ExportBuilder.dict_to_joined_export(
                d, index, indices, survey_name)
            output = ExportBuilder.decode_mongo_encoded_section_names(
                joined_export)
            # attach meta fields (index, parent_index, parent_table)
            # output has keys for every section
            if survey_name not in output:
                output[survey_name] = {}
            output[survey_name][INDEX] = index
            output[survey_name][PARENT_INDEX] = -1
            for section in self.sections:
                # get data for this section and write to csv
                section_name = section['name']
                csv_def = csv_defs[section_name]
                fields = [
                    element['xpath'] for element in
                    section['elements']] + self.EXTRA_FIELDS
                csv_writer = csv_def['csv_writer']
                # section name might not exist within the output, e.g. data was
                # not provided for said repeat - write test to check this
                row = output.get(section_name, None)
                if type(row) == dict:
                    ZippedCsvExportBuilder.write_row(
                        self.pre_process_row(row, section),
                        csv_writer, fields)
                elif type(row) == list:
                    for child_row in row:
                        ZippedCsvExportBuilder.write_row(
                            self.pre_process_row(child_row, section),
                            csv_writer, fields)
