# -*- coding: utf-8 -*-
import time

from urllib.parse import urlencode
from hashlib import md5


def sort_urlencode(data):
    """
    Encode a dict into a URL query string.
    sort by key

    :param dict data: data
    :rtype: str
    """
    return urlencode(sorted(data.items(), key=lambda v: v[0]), doseq=True)


def signature(params, secret, lower=False):
    """
    gen params signature

    :param dict params: req param
    :param str secret: app secret
    :rtype: str
    :return: sign
    """
    encoded_params = sort_urlencode(params)
    if '+' in encoded_params:
        encoded_params = encoded_params.replace('+', '%20')
    if lower:
        encoded_params = encoded_params.lower()
    encoded_params += secret
    return md5(encoded_params.encode()).hexdigest()


def sign_params(params, app_key, secret, lower=False):
    """
    gen params signature with give secret
    return signatured params

    :param dict params: params be signatured
    :param str app_key: app_key
    :param str secret: app secret
    :param bool lower:
    :rtype: str
    :return: bytes signatured params with urlencode
    """
    params['appkey'] = app_key
    params['ts'] = int(time.time())
    sign = signature(params, secret, lower)
    params['sign'] = sign
    return sort_urlencode(params).encode()
