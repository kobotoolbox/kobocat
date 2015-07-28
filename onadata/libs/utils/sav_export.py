from django.core.files.temp import NamedTemporaryFile
from savReaderWriter import SavWriter
from zipfile import ZipFile

from onadata.libs.utils.common_tags import INDEX, PARENT_INDEX
from onadata.libs.utils.export_builder import ExportBuilder


class ZippedSavExportBuilder(ExportBuilder):
    
    @classmethod
    def write_row(cls, row, sav_writer, fields):
        sav_writer.writerow(
            [ExportBuilder.encode_if_str(row, field, True) for field in fields])


    def export(self, path, data, *args):

        sav_defs = {}

        # write headers
        for section in self.sections:
            fields = [element['title'] for element in section['elements']]\
                + self.EXTRA_FIELDS
            c = 0
            var_labels = {}
            var_names = []
            tmp_k = {}
            for field in fields:
                c += 1
                var_name = 'var%d' % c
                var_labels[var_name] = field
                var_names.append(var_name)
                tmp_k[field] = var_name

            var_types = dict(
                [(tmp_k[element['title']],
                  0 if element['type'] in ['decimal', 'int'] else 255)
                 for element in section['elements']]
                + [(tmp_k[item],
                    0 if item in ['_id', '_index', '_parent_index'] else 255)
                   for item in self.EXTRA_FIELDS]
            )
            sav_file = NamedTemporaryFile(suffix=".sav")
            sav_writer = SavWriter(sav_file.name, varNames=var_names,
                                   varTypes=var_types,
                                   varLabels=var_labels, ioUtf8=True)
            sav_defs[section['name']] = {
                'sav_file': sav_file, 'sav_writer': sav_writer}

        index = 1
        indices = {}
        survey_name = self.survey.name
        for d in data:
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
                sav_def = sav_defs[section_name]
                fields = [
                    element['xpath'] for element in
                    section['elements']] + self.EXTRA_FIELDS
                sav_writer = sav_def['sav_writer']
                row = output.get(section_name, None)
                if type(row) == dict:
                    ZippedSavExportBuilder.write_row(
                        self.pre_process_row(row, section),
                        sav_writer, fields)
                elif type(row) == list:
                    for child_row in row:
                        ZippedSavExportBuilder.write_row(
                            self.pre_process_row(child_row, section),
                            sav_writer, fields)
            index += 1

        for section_name, sav_def in sav_defs.iteritems():
            sav_def['sav_writer'].closeSavFile(
                sav_def['sav_writer'].fh, mode='wb')

        # write zipfile
        with ZipFile(path, 'w') as zip_file:
            for section_name, sav_def in sav_defs.iteritems():
                sav_file = sav_def['sav_file']
                sav_file.seek(0)
                zip_file.write(
                    sav_file.name, "_".join(section_name.split("/")) + ".sav")

        # close files when we are done
        for section_name, sav_def in sav_defs.iteritems():
            sav_def['sav_file'].close()

