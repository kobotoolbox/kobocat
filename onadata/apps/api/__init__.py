
import re

import pyxform.odk_validate


#############################################################################
#                                  WARNING
# This is a monkey patch to fix a bug in odk and should be removed as soon as
# the fix is upstream
#############################################################################

def _cleanup_errors(error_message):

    # this is the same code as the original function
    def get_last_item(xpathStr):
        l = xpathStr.split("/")
        return l[len(l) - 1]

    def replace_function(match):
        strmatch = match.group()
        if strmatch.startswith("/html/body") \
                or strmatch.startswith("/root/item") \
                or strmatch.startswith("/html/head/model/bind") \
                or strmatch.endswith("/item/value"):
            return strmatch
        return "${%s}" % get_last_item(match.group())
    pattern = "(/[a-z0-9\-_]+(?:/[a-z0-9\-_]+)+)"
    error_message = re.compile(pattern, flags=re.I).sub(replace_function,
        error_message)
    k = []
    lastline = ''
    for line in error_message.splitlines():
        has_java_filename = line.find('.java:') is not -1
        is_a_java_method = line.find('\tat') is not -1
        is_duplicate = (line == lastline)
        lastline = line
        if not has_java_filename and not is_a_java_method and not is_duplicate:
            if line.startswith('java.lang.RuntimeException: '):
                line = line.replace('java.lang.RuntimeException: ', '')
            if line.startswith('org.javarosa.xpath.XPathUnhandledException: '):
                line = line.replace('org.javarosa.xpath.XPathUnhandledException: ', '')
            if line.startswith('java.lang.NullPointerException'):
                continue
            k.append(line)

    # original value causing UnicodeDecodeError
    #return u'\n'.join(k)

    # Fix:
    return '\n'.join(k).decode('ascii', errors="replace")


pyxform.odk_validate._cleanup_errors = _cleanup_errors
