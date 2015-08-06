# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

# Class code:

import json
from google_connect import GoogleConnect
from wikipedia import WikiFetch

MYSECRET = "behappy"

TABLE_NAMES = {
    'analysis_type': db.analysis_type,
    'pages': db.wikipages,
    'analysis': db.analysis
}


def make_key_pair(a, k):
    return json.dumps([a, k])


def put():
    secret = request.args(0)
    if secret != MYSECRET:
        raise HTTP(400)
    appid = request.args(1)
    key = request.args(2)
    if appid is None or key is None:
        raise HTTP(400)
    content = request.vars.c
    itemkey = make_key_pair(appid, key)
    db.store.update_or_insert(db.store.itemkey == itemkey,
                              itemkey=itemkey,
                              content=content)
    return dict(result='ok')


def get():
    secret = request.args(0)
    if secret != MYSECRET:
        raise HTTP(400)
    appid = request.args(1)
    key = request.args(2)
    if appid is None or key is None:
        raise HTTP(400)

    result = create_task_json(pageid=1, base_revision=2, priority=1)
    return result


def add():
    """Add entries"""
    form = ''
    entry_type = request.args(0) if not None else ''

    if request.args(0):
        try:
            table_name = TABLE_NAMES[entry_type]
            print table_name
        except:
            table_name = ''
            session.flash = T("Incorrect argument.")
            redirect(URL('default', 'index'))

        form = SQLFORM(table_name)
        if form.process().accepted:
            # Successful processing.
            session.flash = T("New Entry inserted")
            redirect(URL('default', 'index'))
    else:
        session.flash = T("No argument provided.")
        redirect(URL('default', 'index'))

    return locals()

@auth.requires_login()
def view():
    form = ''
    entry_type = request.args(0) if not None else ''

    if request.args(0):
        try:
            table_name = TABLE_NAMES[entry_type]
        except:
            table_name = ''
            session.flash = T("Incorrect argument.")
            redirect(URL('default', 'index'))

        form = SQLFORM.grid(table_name)
        print form

    else:
        session.flash = T("No argument provided.")
        redirect(URL('default', 'index'))

    return locals()


def initiate(content=None):
    analysis_entry = Revision(id="131231",
                              pageid=1213,
                              )
    analysis_entry.put()

    g = GoogleConnect()

    g.write_to_bucket(bucket_name="revision_original",
                      file_to_write="testfile.txt",
                      content=content)

    read_text = g.read_from_bucket(bucket_name="revision_original",
                      file_to_write="testfile.txt")

    print read_text
    return read_text


################

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    text = initiate()

    if text is not None:
        response.flash = T(text)
    else:
        response.flash = T("None text")
    return dict(message=T('Hello World'))


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
