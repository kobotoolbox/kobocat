# coding: utf-8
from __future__ import (unicode_literals, print_function,
                        absolute_import, division)

import hashlib

from django.utils.six.moves.urllib.parse import urlencode
from django.utils.six.moves.urllib.request import urlopen

DEFAULT_GRAVATAR = "https://formhub.org/static/images/formhub_avatar.png"
GRAVATAR_ENDPOINT = "https://secure.gravatar.com/avatar/"
GRAVATAR_SIZE = str(60)


def get_gravatar_img_link(user):
    url = GRAVATAR_ENDPOINT +\
        hashlib.md5(user.email.lower()).hexdigest() + "?" + urlencode({
            'd': DEFAULT_GRAVATAR, 's': str(GRAVATAR_SIZE)
        })
    return url


def gravatar_exists(user):
    url = GRAVATAR_ENDPOINT +\
        hashlib.md5(user.email.lower()).hexdigest() + "?" + "d=404"
    exists = urlopen(url).getcode() != 404
    return exists
