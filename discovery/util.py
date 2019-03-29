# -*- coding: utf-8 -*-
from urllib.parse import urlencode


def sort_urlencode(data):
    """
    Encode a dict into a URL query string.
    sort by key

    :param dict data: data
    :rtype: str
    """
    return urlencode(sorted(data.items(), key=lambda v: v[0]), doseq=True)
