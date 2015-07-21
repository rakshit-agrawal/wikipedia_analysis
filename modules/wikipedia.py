#!/usr/bin/env python

# This controller works on communication with Wikipedia.
# All communication of the system to Wikipedia API
# is defined in this file.
#
# Rakshit Agrawal, 2015

from datetime import datetime
import json
import urllib
import urllib2

from pprint import pprint
__author__ = 'rakshit'

DATE_PATTERN = "%a, %d %b %Y %H:%M:%S %z"
WIKI_BASE_URL = "http://en.wikipedia.org/w/api.php"

WIKI_MAX_REVISION_LIMIT = 500  # Update if any change observed. Not used mostly but kept for reference.

############################################################
# Parameter values to be sent for concerned GET requests

WIKI_PARAMS = {
    'revisions': {  # Parameters to fetch revisions for given pageids
        "action": "query",
        "prop": "revisions",
        "format": "json",
        "rvprop": "ids|timestamp|user|userid|size|comment|content|tags|flags|parsetree",
        "rvlimit": "10",
        "pageids": "32927",
        "rvdir": "newer"
    },
    'recent_changes': {  # Parameters to fetch revisions for pages with recent changes
        "action": "query",
        "prop": "revisions",
        "format": "json",
        "indexpageids": "1",
        "generator": "recentchanges",
        "grcdir": "older",
        "grcnamespace": "0",
        "grcprop": "ids",
        "grcshow": "minor",
        "grclimit": "30"

    },
    'category_members': {  # Parameters to fetch list of category members for a given category.
        "action": "query",
        "list": "categorymembers",
        "cmpageid": "44126225",
        "format": "json",
        "cmprop": "ids|title|type",
        "cmlimit": "max",
        "indexpageids": "1",

    },
    'page_info': {  # Parameters for Page Information
        "action": "query",
        "prop": "info",
        "format": "json",
        "pageids": ""
    }
}


def _get(url="", values=None, headers=None):
    # HTTP GET to fetch from external URLs
    """
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
    except Exception, e:
        result = dict(query="Error", error=e)

    return result


class WikiFetch:
    """
    Function structure:

        fetch_* function performs data fetch for the concerned operation.
        parse_* function reads through the data and then calls for additional operations.

    """

    def __init__(self):
        self.ctr = 0

        # Set for all the pages within a given category (includes pages from subcategories)
        self.category_pages = set()

        # Set of subcategoies within a category
        self.subcat_list = set()

        self.page_list = []
        self.depth = 0
        self.nrev = 0

    def get_recent_changes(self):
        """
            Function to fetch recent changes in Wikipedia pages.
            Calls Wikimedia API to getch revision information with
            generator of recent changes.

            Fetch feed for recent changes from Wikipedia.
            Using action=query with generator=recentchanges

            Returns the set of pages.
            :return: A dict of pages with recent changes

        """

        # Get JSON from Wikimedia
        feed = _get(url=WIKI_BASE_URL, values=WIKI_PARAMS['recent_changes'])

        # Get the page set from these changes
        pages = dict()
        for k,v in feed["query"]["pages"].iteritems():
            pageid = v['pageid']  # Page ID
            revid = v['revisions'][0]['revid']  # Last known revision
            title = v['title']  # Title of Page

            # Add entry in the pages dict
            pages[pageid] = dict(last_known_rev = revid, title = title)

        # Return the dict with pageid(key) and last_known_revision and title as values
        return pages

    def fetch_revisions_for_page(self, pageid, start_rev="", chunk_size=10):

        """
            Fetch revisions for page with the given ID.
            Optional argument of starting revision. Mostly used to fetch continuous revisions.

            Using action=query

            Returns entire list of revisions newer than current latest.
        """
        WIKI_PARAMS['revisions']["pageids"] = pageid
        WIKI_PARAMS['revisions']['rvlimit'] = chunk_size
        # WIKI_PARAMS['revisions']["rvendid"] = LATEST_REV[pageid]
        if start_rev != "":
            WIKI_PARAMS['revisions']["rvstartid"] = start_rev

        result = _get(url=WIKI_BASE_URL, values=WIKI_PARAMS['revisions'])
        # print(result)
        new_revisions = self.parse_revisions(revisions=result)
        return new_revisions

    def parse_revisions(self, revisions):
        # Parse through the revisions collected from fetch function.
        # Check if current latest is in the results.
        #   If not, then keep making recursive calls to the fetch-parse function sequence
        # Create a complete list of revisions form all calls before returning it.
        parsed_json = revisions
        pages = parsed_json["query"]["pages"]
        revisions = None
        for i in pages:
            revisions = parsed_json["query"]["pages"][i]["revisions"]
            page_id = parsed_json["query"]["pages"][i]["pageid"]
            print"Length of revisions - {}".format(len(revisions))
            rev_list = []
            for rev in revisions:
                rev_list.append(rev["revid"])
            latest = LATEST_REV[str(page_id)]

            if int(latest) not in rev_list:
                # if len(rev)==WIKI_MAX_REVISION_LIMIT:
                start_id = revisions[-1]["parentid"]  # Get revisions prom last one's parent to our latest
                more_revs = self.fetch_revisions_for_page(str(page_id), start_id)
                revisions += more_revs

        # Return complete list of revisions collected recursively
        return revisions
