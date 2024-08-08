# coding: utf-8
from io import BytesIO
from tempfile import NamedTemporaryFile

import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image

from onadata.libs.utils.viewer_tools import get_path


def flat(*nums):
    """
    Build a tuple of ints from float or integer arguments.
    Useful because PIL crop and resize require integer points.
    source: https://gist.github.com/16a01455
    """

    return tuple(int(round(n)) for n in nums)


def get_dimensions(size_, longest_side):
    width, height = size_
    if width > height:
        height = (height / width) * longest_side
        width = longest_side
    elif height > width:
        width = (width / height) * longest_side
        height = longest_side
    else:
        height = longest_side
        width = longest_side
    return flat(width, height)


def _save_thumbnails(image, original_path, size, suffix):
    # Thumbnail format will be set by original file extension.
    # Use same format to keep transparency of GIF/PNG
    nm = NamedTemporaryFile(suffix='.%s' % image.format)
    try:
        # Ensure conversion to float in operations
        image.thumbnail(get_dimensions(image.size, float(size)), Image.LANCZOS)
    except ZeroDivisionError:
        pass
    try:
        image.save(nm.name)
    except IOError:
        # e.g. `IOError: cannot write mode P as JPEG`, which gets raised when
        # someone uploads an image in an indexed-color format like GIF
        image.convert('RGB').save(nm.name)

    # Try to delete file with the same name if it already exists to avoid useless file.
    # i.e if `file_<suffix>.jpg` exists, Storage will save `a_<suffix>_<random_string>.jpg`
    # but nothing in the code is aware about this `<random_string>
    try:
        default_storage.delete(get_path(original_path, suffix))
    except IOError:
        pass

    default_storage.save(
        get_path(original_path, suffix), ContentFile(nm.read()))

    nm.close()


def resize(filename):
    is_local = default_storage.__class__.__name__ == 'FileSystemStorage'
    image = None
    original_path = None

    if is_local:
        path = default_storage.path(filename)
        image = Image.open(path)
        original_path = filename
    else:
        path = default_storage.url(filename)
        original_path = filename
        req = requests.get(path)
        if req.status_code == 200:
            im = BytesIO(req.content)
            image = Image.open(im)

    if image:
        conf = settings.THUMB_CONF
        [_save_thumbnails(
            image, original_path,
            conf[key]['size'],
            conf[key]['suffix']) for key in settings.THUMB_ORDER]


def image_url(attachment, suffix):
    """
    Return url of an image given size(@param suffix)
    e.g large, medium, small, or generate required thumbnail
    """
    url = attachment.media_file.url
    if suffix == 'original':
        return url
    else:
        if suffix in settings.THUMB_CONF:
            size = settings.THUMB_CONF[suffix]['suffix']
            filename = attachment.media_file.name
            if default_storage.exists(filename):
                if default_storage.exists(get_path(filename, size)) and \
                        default_storage.size(get_path(filename, size)) > 0:
                    url = default_storage.url(
                        get_path(filename, size))
                else:
                    resize(filename)
                    return image_url(attachment, suffix)
            else:
                return None
    return url
