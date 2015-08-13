import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

__author__ = 'rakshit'


class Analysis(ndb.Model):
    type = ndb.StringProperty()
    result = ndb.FloatProperty()  # Main property coming out of an analysis (eg., overall trust)
    values = ndb.JsonProperty()  # This can hold a dict of all other values within that analysis
    annotated_dump = ndb.StringProperty()  # This should be the GCS item path


class Revision(ndb.Model):
    revision_id = ndb.IntegerProperty()  # RevID as an integer entry for itself
    name = ndb.StringProperty()  # RevID same as wikipedia in String format
    pageid = ndb.IntegerProperty()  # PageID same as wikipedia
    userid = ndb.StringProperty()  # UserID same as wikipedia
    username = ndb.StringProperty()  # username from Wikipedia
    revision_date = ndb.DateTimeProperty()  # Time when revision was submitted to Wikipedia
    gcs_key = ndb.StringProperty()


class AuthorReputation(ndb.Model):
    userid = ndb.StringProperty()
    reputation = ndb.FloatProperty()
    # last_updated = ndb.DateTimeProperty(auto_update_now=True) # check the auto_now vs. auto_update_now?


class AuthorshipMedatada(ndb.Model):
    revision_id = ndb.IntegerProperty()
    # ... 
    gcs_key = ndb.StringProperty()  # check


class RevisionTrust(ndb.Model):
    revision_id = ndb.IntegerProperty()  # RevID as an integer entry for itself
    name = ndb.StringProperty()  # RevID same as wikipedia in String format
    pageid = ndb.IntegerProperty()  # PageID same as wikipedia
    userid = ndb.StringProperty()  # UserID same as wikipedia
    username = ndb.StringProperty()  # username from Wikipedia
    revision_date = ndb.DateTimeProperty()  # Time when revision was submitted to Wikipedia
    gcs_key = ndb.StringProperty()


NDB_MODELS = {
    'revision_original': Revision,
    'trust': RevisionTrust,
}

ALGO_META = {
    'revision_original': {'x-goog-meta-origninal': True,
                          'x-goog-meta-algorithm': None},
    'trust': {'x-goog-meta-origninal': False,
              'x-goog-meta-algorithm': 'trust'},
}
