from datetime import datetime

from openpyxl.date_time import SharedDate
from openpyxl.workbook import Workbook

from onadata.libs.utils.common_tags import INDEX, PARENT_INDEX, PARENT_TABLE_NAME
from onadata.libs.utils.export_builder import ExportBuilder


class XlsExportBuilder(ExportBuilder):

    # Configuration options
    group_delimiter = '/'
    split_select_multiples = True
    binary_select_multiples = False
    
    CONVERT_FUNCS = {
        'int': lambda x: int(x),
        'decimal': lambda x: float(x),
        'date': lambda x: XlsExportBuilder.string_to_date_with_xls_validation(x),
        'dateTime': lambda x: datetime.strptime(x[:19], '%Y-%m-%dT%H:%M:%S')
    }

    def __init__(self, xform, config):
        super(XlsExportBuilder, self).__init__(xform, config)
        self.group_delimiter = config['group_delimiter']
        self.split_select_multiples = config['split_select_multiples']
        self.binary_select_multiples = config['binary_select_multiples']
        
    @classmethod
    def string_to_date_with_xls_validation(cls, date_str):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        try:
            SharedDate().datetime_to_julian(date_obj)
        except ValueError:
            return date_str
        else:
            return date_obj
    
    @classmethod
    def write_row(cls, data, work_sheet, fields, work_sheet_titles):
        # update parent_table with the generated sheet's title
        data[PARENT_TABLE_NAME] = work_sheet_titles.get(
            data.get(PARENT_TABLE_NAME))
        work_sheet.append([data.get(f) for f in fields])
            
    def export(self, path, data, *args):
        wb = Workbook(optimized_write=True)
        work_sheets = {}
        # map of section_names to generated_names
        work_sheet_titles = {}
        for section in self.sections:
            section_name = section['name']
            work_sheet_title = self.get_valid_sheet_name(
                "_".join(section_name.split("/")), work_sheet_titles.values())
            work_sheet_titles[section_name] = work_sheet_title
            work_sheets[section_name] = wb.create_sheet(
                title=work_sheet_title)

        # write the headers
        for section in self.sections:
            section_name = section['name']
            headers = [
                element['title'] for element in
                section['elements']] + self.EXTRA_FIELDS
            # get the worksheet
            ws = work_sheets[section_name]
            ws.append(headers)

        indices = {}
        survey_name = self.survey.name
        for index, d in enumerate(data, 1):
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
                # get data for this section and write to xls
                section_name = section['name']
                fields = [
                    element['xpath'] for element in
                    section['elements']] + self.EXTRA_FIELDS

                ws = work_sheets[section_name]
                # section might not exist within the output, e.g. data was
                # not provided for said repeat - write test to check this
                row = output.get(section_name, None)
                if type(row) == dict:
                    XlsExportBuilder.write_row(
                        self.pre_process_row(row, section),
                        ws, fields, work_sheet_titles)
                elif type(row) == list:
                    for child_row in row:
                        XlsExportBuilder.write_row(
                            self.pre_process_row(child_row, section),
                            ws, fields, work_sheet_titles)
                        
        wb.save(filename=path)
