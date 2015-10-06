from http_requests import _get, _post
from credentials import CLIENT_ID, CLIENT_SECRET
__author__ = 'rakshit'


def get_access_token(CLIENT_ID, CLIENT_SECRET):

    url = "https://accounts.google.com/o/oauth2/auth"
    values = dict(client_id=CLIENT_ID,
                  #client_secret=CLIENT_SECRET,
                  scope="https://www.googleapis.com/auth/devstorage.full_control",
                  response_type = "token",
                  redirect_uri = "http://wikitrust-test.appspot.com/wikipedia_analysis"
                  )
    token = _post(url, values=values)



    return token
