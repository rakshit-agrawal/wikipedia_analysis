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
                    "rvprop": "ids|timestamp|user|userid|size|comment|content|tags",  # |parsetree",
                    "rvlimit": "10",
                    "pageids": "32927",
                    "rvdir": "newer"
                    },
    'recent_changes': {  # Parameters to fetch revisions for pages with recent changes
                         "action": "query",
                         "prop": "revisions",
                         "format": "json",
                         "rvprop":"ids|timestamp|user|userid",
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
                    },
    'user_contributions': {  # Parameters to fetch revisions for given pageids
                             "action": "query",
                             "list": "usercontribs",
                             "format": "json",
                             "ucprop": "ids|title|timestamp|sizediff|tags|size|comment",
                             "uclimit": "10",
                             "ucuser": "",
                             "ucdir": "newer",
                             "ucnamespace": "0",
                             },
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
    except urllib2.HTTPError as e:
        print e.code
        print e.read()

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

    @staticmethod
    def get_recent_changes():
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
        print feed
        # Get the page set from these changes
        pages = dict()
        for k, v in feed["query"]["pages"].iteritems():
            pageid = v['pageid']  # Page ID
            revid = v['revisions'][0]['revid']  # Last known revision
            title = v['title']  # Title of Page
            user = v['revisions'][0]['user']  # User editing the revision. Contains IP address if not a logged in user
            userid = v['revisions'][0]['userid'] # User ID of the user. 0 is user is an IP address

            # Add entry in the pages dict
            pages[pageid] = dict(last_known_rev=revid,
                                 title=title,
                                 user = user,
                                 userid = userid)

        # Return the dict with pageid(key) and value as a dict with keys:
        # last_known_revision, title, user and userid
        return pages

    def fetch_revisions_for_page(self, pageid=None, start_rev=None, chunk_size=10, continuous=False):
        """
        This function connects to Wikipedia and extracts all data for revisions
        of page with pageid.
        Optional parameters of chunk size and continuous are used to set the number of
        revisions to fetch.
        start_rev is used to set a starting revision ID in retrieval process.

        The revisions are retrieved in the direction from oldest to newest

        :rtype : List of revisions
        :param pageid: Wikipedia pageid
        :param start_rev: Starting revision for pageid
        :param chunk_size: Chunk size for number of revisions to fetch (max 50)
        :param continuous: Boolean to fetch all possible revisions available
        :return:
        """

        # Setting parameters in GET request dict
        WIKI_PARAMS['revisions']["pageids"] = pageid
        WIKI_PARAMS['revisions']['rvlimit'] = chunk_size

        # Set start ID if provided. Else it remains None which means
        # revisions start at the very first revision of page
        if start_rev is not None and start_rev != "null":
            WIKI_PARAMS['revisions']["rvstartid"] = start_rev

        # GET the revisions from Wikipedia
        result = _get(url=WIKI_BASE_URL, values=WIKI_PARAMS['revisions'])

        # Extract revision list from resulting json
        revisions = result["query"]["pages"][pageid]["revisions"]
        # Check for continuous
        if continuous:
            # Recursively fetch all available revisions till latest

            # Set latest revision of retrieved revisions as start id of next
            # revision fetch.
            new_start_rev = revisions[-1]['revid']

            # Check for revision being actual latest by measuring revision list length
            if len(revisions) > 1:
                # If more than one revisions available then we may not have
                # reached the latest revision yet.

                # Remove the last entry in revisions since it is now being
                # retrieved again.
                revisions.pop(-1)

                # Add new revisions by recursively calling this function
                revisions += self.fetch_revisions_for_page(pageid=pageid,
                                                           start_rev=new_start_rev,
                                                           continuous=True)

                # Else case not required here because revisions are completely
                # updated at this point if only latest revision has been fetched.

        # Else case not required in continuous check.
        # In the absence of continuity, only the revisions from first retrieval are returned.

        # Return complete list of revisions as requested in the call
        return revisions

    def get_user_contributions(self, username=None, start_time=None, end_time=None, cont_limit=20):
        """
        This function connects to Wikipedia and fetches edits done by a user
        on Wikipedia.
        The results of this function can then be used to retrieve corresponding revision data.
        :param username:
        :param start_time:
        :param end_time:
        :param cont_limit:
        :return:
        """

        # Setting parameters in GET request dict
        WIKI_PARAMS['user_contributions']["ucuser"] = username
        WIKI_PARAMS['user_contributions']['uclimit'] = cont_limit

        # Set start ID if provided. Else it remains None which means
        # contributions start at the very first revision of page
        if start_time is not None and start_time != "null":
            WIKI_PARAMS['user_contributions']["ucstart"] = start_time

        # GET the user contributions from Wikipedia
        result = _get(url=WIKI_BASE_URL, values=WIKI_PARAMS['user_contributions'])

        # Extract user contribution list from resulting json
        contributions = result["query"]["usercontribs"]

        return contributions
