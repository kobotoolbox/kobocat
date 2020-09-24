# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
#!/usr/bin/env python
# encoding: utf-8

'''
    Wrapper script around common use of i18n.

    1. Add new language: creates PO files and instruct how to add to transifex.

    2. Update languages: Regenerate English PO files. TX gets it automaticaly.

    3. Update translations: download translations from TX and compiles them.
'''

import os
import sys
import StringIO
import tempfile
import types
import shutil
import contextlib

import twill
from twill import commands as tw, get_browser
from twill.errors import TwillAssertionError
from clint import args
from clint.textui import puts, colored, indent
from shell_command import shell_call

# List of languages we care about
LANGS = ['en', 'fr', 'es', 'it', 'nl', 'zh', 'ne', 'km']
I18N_APPS = ['onadata.apps.main', 'onadata.apps.viewer']

TX_LOGIN_URL = 'https://www.transifex.com/signin/'
REPO_ROOT = os.join('..', os.path.dirname(os.path.abspath(__file__)))


class DownloadFailed(StandardError):
    pass


@contextlib.contextmanager
def chdir(dirname):
    curdir = os.getcwd()
    try:
        os.chdir(dirname)
        yield
    finally:
        os.chdir(curdir)


def download_with_login(url, login_url, login=None,
                        password=None, ext='',
                        username_field='username',
                        password_field='password',
                        form_id=1):
    ''' Download a URI from a website using Django by loging-in first

        1. Logs in using supplied login & password (if provided)
        2. Create a temp file on disk using extension if provided
        3. Write content of URI into file '''

    # log-in to Django site
    if login and password:
        tw.go(login_url)
        tw.formvalue('%s' % form_id, username_field, login)
        tw.formvalue('%s' % form_id, password_field, password)
        tw.submit()

    # retrieve URI
    try:
        tw.go(url)
        tw.code('200')
    except TwillAssertionError:
        code = get_browser().get_code()
        # ensure we don't keep credentials
        tw.reset_browser()
        raise DownloadFailed("Unable to download %(url)s. "
                             "Received HTTP #%(code)s."
                             % {'url': url, 'code': code})
    buff = StringIO.StringIO()
    twill.set_output(buff)
    try:
        tw.show()
    finally:
        twill.set_output(None)
        tw.reset_browser()

    # write file on disk
    suffix = '.%s' % ext if ext else ''
    fileh, filename = tempfile.mkstemp(suffix=suffix)
    os.write(fileh, buff.getvalue())
    os.close(fileh)
    buff.close()

    return filename


def getlangs(lang):
    if not lang:
        return LANGS
    if isinstance(lang, types.ListType):
        return lang
    return [lang, ]


def add(lang):
    langs = getlangs(lang)
    puts("Adding %s" % ', '.join(langs))
    for loc in langs:
        with indent(2):
            puts("Generating PO for %s" % loc)
        shell_call("django-admin.py makemessages -l %(lang)s "
                   "-e py,html,email,txt" % {'lang': loc})
        for app in I18N_APPS:
            with indent(4):
                puts("Generating PO for app %s" % app)
            with chdir(os.path.join(REPO_ROOT, app)):
                shell_call("django-admin.py makemessages "
                           "-d djangojs -l %(lang)s" % {'lang': loc})
        puts(colored.green("sucesssfuly generated %s" % loc))


def update(user, password, lang=None):
    langs = getlangs(lang)
    puts("Updating %s" % ', '.join(langs))
    for loc in langs:
        with indent(2):
            puts("Downloading PO for %s" % loc)
        url = ('https://www.transifex.com/projects/p/formhub/'
               'resource/django/l/%(lang)s/download/for_use/' % {'lang': loc})
        try:
            tmp_po_file = download_with_login(url, TX_LOGIN_URL,
                                              login=user, password=password,
                                              ext='po',
                                              username_field='identification',
                                              password_field='password',
                                              form_id=1)
            po_file = os.path.join(REPO_ROOT, 'locale', loc,
                                   'LC_MESSAGES', 'django.po')
            with indent(2):
                puts("Copying downloaded file to %s" % po_file)
            shutil.move(tmp_po_file, po_file)
        except Exception as e:
            puts(colored.red("Unable to update %s "
                             "from Transifex: %r" % (loc, e)))
        puts(colored.green("sucesssfuly retrieved %s" % loc))
    compile_mo(langs)


def compile_mo(lang=None):
    langs = getlangs(lang)
    puts("Compiling %s" % ', '.join(langs))
    for loc in langs:
        with indent(2):
            puts("Compiling %s" % loc)
        shell_call("django-admin.py compilemessages -l %(lang)s "
                   % {'lang': loc})
        for app in I18N_APPS:
            with indent(4):
                puts("Compiling app %s" % app)
            with chdir(os.path.join(REPO_ROOT, app)):
                shell_call("django-admin.py compilemessages -l %(lang)s"
                           % {'lang': loc})
        puts(colored.green("sucesssfuly compiled %s" % loc))


def usage(exit=True, code=1):
    print("i18n wrapper script for formhub.\n")
    with indent(4):
        puts(colored.yellow(",/i18ntool.py add --lang <lang>"))
        puts("Create required files for enabling translation "
             "of language with code <lang>\n")

        puts(colored.yellow("./i18ntool.py refresh [--lang <lang>]"))
        puts("Update the PO file for <lang> based on code.\n"
             "<lang> is optionnal as we only use EN and do "
             "all translations in Transifex.\n")

        puts(colored.yellow("./i18ntool.py update --user <tx_user> "
                            "--password <tx_pass> [--lang <lang>]"))
        puts("Downloads new PO files for <lang> (or all) from Transifex "
             "then compiles new MO files\n")

        puts(colored.yellow("./i18ntool.py compile [--lang <lang>]"))
        puts("Compiles all PO files for <lang> (or all) into MO files.\n"
             "Not required unless you want to.\n")

    if exit:
        sys.exit(code)


COMMANDS = {
    'add': add,
    'refresh': add,
    'update': update,
    'compile': compile_mo,
    'usage': usage,
    'help': usage
}


def main():

    try:
        command = COMMANDS.get(args.all.pop(0).lower(), usage)
    except:
        command = usage

    # fallback to usage.
    if command is usage:
        return command()

    # retrieve lang
    try:
        lang = args.grouped.get('lang', []).pop(0)
        if lang not in LANGS:
            raise ValueError("Unknown lang code")
    except ValueError as e:
        puts(colored.red(e.message))
        usage()
    except IndexError:
        lang = None

    # update cmd requires more args.
    if command is update:
        # extract user & password
        try:
            user = args.grouped.get('--user', []).pop(0)
            password = args.grouped.get('--password', []).pop(0)
        except:
            raise
            user = password = None

        if not user or not password:
            print(colored.red(
                "You need to provide Transifex.com credentials"))
            usage()

        return command(user, password, lang)

    # execute command with lang argument.
    return command(lang)


if __name__ == '__main__':
    main()
