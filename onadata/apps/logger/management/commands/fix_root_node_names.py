import time
from xml.dom import minidom
from django.core.management.base import BaseCommand, CommandError
from onadata.apps.logger.models import XForm, Instance

AUTO_NAME_INSTANCE_XML_SEARCH_STRING = 'uploaded_form_'

def replace_first_and_last(s, old, new):
    s = s.replace(old, new, 1)
    # credit: http://stackoverflow.com/a/2556252
    return new.join(s.rsplit(old, 1))

def get_xform_root_node_name(xform):
    parsed = minidom.parseString(xform.xml.encode('utf-8'))
    instance_xml = parsed.getElementsByTagName('instance')[0]
    root_node_name = None
    for child in instance_xml.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            root_node_name = child.nodeName
            break
    return root_node_name

def write_same_line(stdout, output, last_len=[0]):
    stdout.write(u'\r{}'.format(output), ending='')
    this_len = len(output)
    too_short = last_len[0] - this_len
    last_len[0] = this_len
    if too_short > 0:
        stdout.write(' ' * too_short, ending='')
    stdout.flush()

class Command(BaseCommand):
    ''' This command cleans up inconsistences between the root instance node
    name specified in the form XML and the actual instance XML. Where a
    discrepancy exists, the instance will be changed to match the form.
    The cause of these mismatches is documented at
    https://github.com/kobotoolbox/kobocat/issues/222. See also
    https://github.com/kobotoolbox/kobocat/issues/242. '''

    help = 'fixes instances whose root node names do not match their forms'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minimum-instance-id',
            type=int,
            help='consider only instances whose ID is greater than or equal '\
                 'to this number'
        )
        parser.add_argument(
            '--minimum-form-id',
            type=int,
            help='consider only forms whose ID is greater than or equal '\
                 'to this number'
        )
        parser.add_argument(
            '--username',
            help='consider only forms belonging to a particular user'
        )

    def handle(self, *args, **options):
        t0 = time.time()
        forms_complete = 0
        mismatch_count = 0
        failed_forms = 0
        failed_instances = 0
        criteria = {'xml__contains': AUTO_NAME_INSTANCE_XML_SEARCH_STRING}
        if options['minimum_instance_id']:
            criteria['id__gte'] = options['minimum_instance_id']
        if options['username']:
            criteria['xform__user__username'] = options['username']
        last_instance = Instance.objects.last()
        kpi_auto_named_instances = Instance.objects.filter(**criteria)
        affected_xforms = XForm.objects.filter(
            id__in=kpi_auto_named_instances.values_list(
                'xform_id', flat=True).distinct()
        ).order_by('id')
        if options['minimum_form_id']:
            affected_xforms = affected_xforms.filter(
                id__gte=options['minimum_form_id'])
        if options['verbosity']:
            self.stdout.write('Running slow query... ', ending='')
            self.stdout.flush()
        total_forms = affected_xforms.count()
        for xform in affected_xforms.iterator():
            try:
                xform_root_node_name = get_xform_root_node_name(xform)
            except Exception as e:
                if options['verbosity']:
                    self.stderr.write(
                        '!!! Failed to get root node name for form {}: ' \
                        '{}'.format(xform.id, e.message)
                    )
                failed_forms += 1
                continue
            affected_instances = xform.instances.exclude(
                xml__endswith='</{}>'.format(xform_root_node_name)
            ).order_by('id')
            for instance in affected_instances:
                try:
                    root_node_name = instance.get_root_node_name()
                except Exception as e:
                    if options['verbosity']:
                        self.stderr.write(
                            '!!! Failed to get root node name for instance ' \
                            '{}: {}'.format(instance.id, e.message)
                        )
                    failed_instances += 1
                    continue
                # Our crude `affected_instances` filter saves us a lot of work,
                # but it doesn't account for things like trailing
                # whitespace--so there might not really be a discrepancy
                if xform_root_node_name != root_node_name:
                    instance.xml = replace_first_and_last(
                        instance.xml, root_node_name, xform_root_node_name)
                    instance.save(force=True)
                    mismatch_count += 1
                if options['verbosity'] > 1:
                    write_same_line(
                        self.stdout,
                        u'Form {} ({}): corrected instance {}. ' \
                        'Completed {} of {} forms.'.format(
                            xform_root_node_name,
                            xform.id,
                            instance.id,
                            forms_complete,
                            total_forms
                    ))
            forms_complete += 1
            if options['verbosity'] > 1:
                write_same_line(
                    self.stdout,
                    u'Form {} ({}). Completed {} of {} forms.'.format(
                        xform_root_node_name,
                        xform.id,
                        forms_complete,
                        total_forms
                ))
        t1 = time.time()
        if options['verbosity']:
            self.stdout.write('')
            self.stdout.write(
                'Corrected {} instances in {} minutes and {} seconds.'.format(
                    mismatch_count,
                    int((t1 - t0) / 60),
                    (t1 - t0) % 60
            ))
            if failed_forms or failed_instances:
                self.stderr.write(
                    'Failed to process {} forms and {} instances'.format(
                        failed_forms, failed_instances
                    )
                )
            self.stdout.write(
                'At the start of processing, the last instance ID ' \
                'was {}.'.format(last_instance.id)
            )
