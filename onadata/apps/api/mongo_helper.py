# -*- coding: utf-8 -*-
import base64
import re

from onadata.libs.utils.common_tags import NESTED_RESERVED_ATTRIBUTES


class MongoHelper(object):

    KEY_WHITELIST = ['$or', '$and', '$exists', '$in', '$gt', '$gte',
                     '$lt', '$lte', '$regex', '$options', '$all']

    @classmethod
    def to_readable_dict(cls, d):
        """
        Updates encoded attributes of a dict with human-readable attributes.
        For example:
        { "myLg==attribute": True } => { "my.attribute": True }

        :param d: dict
        :return: dict
        """

        for key, value in list(d.items()):
            if type(value) == list:
                value = [cls.to_readable_dict(e)
                         if type(e) == dict else e for e in value]
            elif type(value) == dict:
                value = cls.to_readable_dict(value)

            if cls._is_attribute_encoded(key):
                del d[key]
                d[cls.decode(key)] = value

        return d

    @classmethod
    def to_safe_dict(cls, d, reading=False):
        """
        Updates invalid attributes of a dict with encoded 'mongo compliant' attributes.

        :param d: dict
        :param reading: boolean.
        :return: dict
        """
        for key, value in list(d.items()):
            if type(value) == list:
                value = [cls.to_safe_dict(e, reading=reading)
                         if type(e) == dict else e for e in value]
            elif type(value) == dict:
                value = cls.to_safe_dict(value, reading=reading)
            elif key == '_id':
                try:
                    d[key] = int(value)
                except ValueError:
                    # if it is not an int don't convert it
                    pass

            if cls._is_nested_reserved_attribute(key):
                # If we want to write into Mongo, we need to transform the dot delimited string into a dict
                # Otherwise, for reading, Mongo query engine reads dot delimited string as a nested object.
                # Drawback, if a user uses a reserved property with dots, it will be converted as well.
                if not reading and key.count(".") > 0:
                    tree = {}
                    t = tree
                    parts = key.split(".")
                    last_index = len(parts) - 1
                    for index, part in enumerate(parts):
                        v = value if index == last_index else {}
                        t = t.setdefault(part, v)
                    del d[key]
                    first_part = parts[0]
                    if first_part not in d:
                        d[first_part] = {}

                    # We update the main dict with new dict.
                    # We use dict_for_mongo again on the dict to ensure, no invalid characters are children
                    # elements
                    d[first_part].update(cls.to_safe_dict(tree[first_part]))

            elif cls.is_attribute_invalid(key):
                del d[key]
                d[cls.encode(key)] = value

        return d

    @staticmethod
    def encode(key):
        """
        Encodes invalid characters of an attribute
        :param key: string
        :return: string
        """
        return reduce(lambda s, c: re.sub(c[0], base64.b64encode(c[1]), s),
                      [(r'^\$', '$'), (r'\.', '.')], key)

    @staticmethod
    def decode(key):
        """
        Decodes invalid characters of an attribute
        :param key: string
        :return: string
        """
        re_dollar = re.compile(r"^%s" % base64.b64encode("$"))
        re_dot = re.compile(r"\%s" % base64.b64encode("."))
        return reduce(lambda s, c: c[0].sub(c[1], s),
                      [(re_dollar, '$'), (re_dot, '.')], key)

    @classmethod
    def is_attribute_invalid(cls, key):
        """
        Checks if an attribute can't be passed to Mongo as is.
        :param key:
        :return:
        """
        return key not in \
               cls.KEY_WHITELIST and (key.startswith('$') or key.count('.') > 0)

    @classmethod
    def _is_attribute_encoded(cls, key):
        """
        Checks if an attribute has been encoded when saved in Mongo.

        :param key: string
        :return: string
        """
        return key not in \
               cls.KEY_WHITELIST and (key.startswith(base64.b64encode("$")) or key.count(base64.b64encode(".")) > 0)

    @staticmethod
    def _is_nested_reserved_attribute(key):
        """
        Checks if key starts with one of variables values declared in NESTED_RESERVED_ATTRIBUTES

        :param key: string
        :return: boolean
        """
        for reserved_attribute in NESTED_RESERVED_ATTRIBUTES:
            if key.startswith(u"{}.".format(reserved_attribute)):
                return True
        return False