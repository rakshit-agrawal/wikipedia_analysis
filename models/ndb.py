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
    name = ndb.StringProperty(indexed=True)  # RevID same as wikipedia
    pageid = ndb.IntegerProperty()  # PageID same as wikipedia
    userid = ndb.StringProperty()  # UserID same as wikipedia
    username = ndb.StringProperty()  # username from Wikipedia
    revision_date = ndb.DateTimeProperty()  # Time when revision was submitted to Wikipedia
    #annotation_date = ndb.DateTimeProperty()  # Time when annotation was performed (optional)
    analysis = ndb.StructuredProperty(Analysis,       # This will allow different kind of analysis
                                      repeated=True)  # to be associated with same revision
