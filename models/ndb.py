import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

__author__ = 'rakshit'


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
