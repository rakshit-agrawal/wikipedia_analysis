import json
import urllib
import urllib2

__author__ = 'rakshit'

def _post(url="", values=None, headers=None):
    """
    HTTP POST to post on to external URLs

    :param url:
    :param values:
    :param headers:
    :return:
    """
    if not headers:
        headers = {}
    if not values:
        values = {}
    try:
        data = urllib.urlencode(values)
        req = urllib2.Request(url=url, data=data, headers=headers)
        response = urllib2.urlopen(req)
        result = response.read()
        result = json.loads(result)

    except urllib2.HTTPError as e:
        print e.code
        print e.read()
        result = dict(query="Error", error=e.read())


    except KeyError, e:
        print e
        result = dict(query="Error", error=e)


    except Exception, e:
        result = dict(query="Error", error=e)

    return result


def _get(url="", values=None, headers=None):
    """
    HTTP GET to fetch from external URLs

    :param url: str
    :param values: dict
    :param headers: dict
    :return:dict
    """
    if not headers:
        headers = {}
    if not values:
        values = {}
    try:
        data = urllib.urlencode(values)
        url = url + "?" + data
        req = urllib2.Request(url=url, headers=headers)
        response = urllib2.urlopen(req)
        result = response.read()
        result = json.loads(result)

    except urllib2.HTTPError as e:
        print e.code
        print e.read()
        result = dict(query="Error", error=e.read())


    except KeyError, e:
        print e
        result = dict(query="Error", error=e)


    except Exception, e:
        result = dict(query="Error", error=e)
    return result