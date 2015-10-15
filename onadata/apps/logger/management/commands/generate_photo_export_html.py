import os
import json
import zipfile
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from django.contrib.auth.models import User
from onadata.apps.logger.models.attachment import Attachment
from tempfile import NamedTemporaryFile
from django.conf import settings
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = ugettext_lazy("Build a simple HTML export with all imgs for a form")
    option_list = BaseCommand.option_list

    def handle(self, *args, **kwargs):
        site_domain = 'https://%s' % Site.objects.first().domain
        user = User.objects.get(username=args[0])
        xform = user.xforms.get(id_string=args[1])
        attachments = Attachment.objects.filter(instance__xform=xform)
        out_strs = []
        export_dir_name = 'tmp_html_export'
        export_dir_path = os.path.join('onadata', 'static', export_dir_name)
        if not os.path.exists(export_dir_path):
            os.mkdir(export_dir_path)

        fileroot = "%s__%s" % (user.username, xform.id_string)
        fileurl = os.path.join(export_dir_name, '%s.zip' % fileroot)
        out_path = "onadata/static/%s" % (fileurl)
        out_url = ''.join([settings.STATIC_URL, fileurl])
        for attachment in attachments.all():
            im_html = """<li><a href="%s/attachment/original?media_file=%s">%s</a></li>""" % (
                    site_domain,
                    attachment.media_file.name,
                    attachment.filename,
                )
            out_strs.append(im_html)
        user_form_json = json.dumps({
                    'username': user.username,
                    'id_string': xform.id_string,
                })

        zf = zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED)

        def build_html_string(title, body):
            out = "<!DOCTYPE html>" + \
                    "<html><head><title> " + title + \
                    "</title></head>" + \
                    "<body>" + body + "</body>" + \
                    "</html>"
            return out

        def put_contents_in_zip(arcname, contents):
            with NamedTemporaryFile() as tf:
                tf.write(contents)
                tf.seek(0)
                zf.write(tf.name, arcname)
        _ol = '<ol>' + '\n'.join(out_strs) + '</ol>'
        full_html = build_html_string(user_form_json, _ol)
        put_contents_in_zip("full.html", full_html)

        print "wrote html file to '%s' with %d attachment urls." % \
            (out_path, len(out_strs))
        print "accessible at %s%s" % (site_domain, out_url)
