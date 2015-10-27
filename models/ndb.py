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


class RevisionQuality(ndb.Model):
    revision_id = ndb.IntegerProperty()  # RevID as an integer for the revision
    name = ndb.StringProperty()  # RevID same as wikipedia in String format
    pageid = ndb.IntegerProperty()  # PageID same as wikipedia
    userid = ndb.StringProperty()  # UserID same as wikipedia
    username = ndb.StringProperty()  # username from Wikipedia
    revision_date = ndb.DateTimeProperty()  # Time when revision was submitted to Wikipedia
    gcs_key = ndb.StringProperty()  # Google Cloud Storage key for the revision
    char_added = ndb.IntegerProperty()  # Count for the number of characters added in this edit
    char_deleted = ndb.IntegerProperty()  # Count for the number of characters deleted in this edit
    position_in_page = ndb.IntegerProperty()  # Position inside the page for change
    spread = ndb.BooleanProperty()  # 1 id spread, 0 is single block
    tdelta_page = ndb.FloatProperty()  # time difference in hours from last edit on this page
    tdelta_author = ndb.FloatProperty()  # time difference in hours from last edit by this author
    tdelta_author_page = ndb.FloatProperty()  # time difference in hours from last edit by this author on this page


NDB_MODELS = {
    'revision_original': Revision,
    'trust': RevisionTrust,
    'reputation': RevisionQuality
}

ALGO_META = {
    'revision_original': {'x-goog-meta-origninal': True,
                          'x-goog-meta-algorithm': None},
    'trust': {'x-goog-meta-origninal': False,
              'x-goog-meta-algorithm': 'trust'},
    'reputation': {'x-goog-meta-origninal': False,
                   'x-goog-meta-algorithm': 'trust'},
}
