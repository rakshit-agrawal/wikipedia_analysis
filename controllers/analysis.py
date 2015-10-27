#!/usr/bin/env python

"""
This file defines the code for server functions taking
care of the analysis generation, assignment and completion process

For web2py, it defines the Analysis controller

This controller takes care of the following functions:
- Generating analysis needs for pages with recent changes
- Assigning analyses to users upon request
- Closing analyses when completed or when time limit elapsed
- Updating last_annotated revisions of every analysis


Rakshit Agrawal, 2015
"""
import json
from datetime import datetime
import logging
from pprint import pprint
import random

from wikipedia import WikiFetch, WIKI_PARAMS, WIKI_BASE_URL, _get

from google_connect import GoogleConnect

__author__ = 'rakshit'

MYSECRET = "secretcode"

CHUNK_SIZE = 10

ALGO_META = {
    'revision_original': {'x-goog-meta-origninal': "True",
                          'x-goog-meta-algorithm': "None"},
    'trust': {'x-goog-meta-origninal': "False",
              'x-goog-meta-algorithm': 'trust'},
}


def _get_analysis_type_from_db():
    """
    This function provides analysis types present in DB table analysis_type.
    It is used to generate a dict of existing analysis in
    the system for use by generate function

    :rtype : dict
    :return: Dict with keys as DB ID and value as analysis_type name
    """
    ret_dict = {}  # Initialize an empty dict

    analysis_types = db().select(db.analysis_type.id, db.analysis_type.name)
    for entry in analysis_types:
        ret_dict[entry.id] = (entry.name, entry.for_page)

    return ret_dict


def _generate_worker_id():
    """
    Generate a random worker ID.

    :return: String version for the 64 bit random value
    """
    val = random.getrandbits(64)
    return str(val)


def _get_page_priority(pageid=None):
    """
    Generate priority value for a given Page ID.
    At present only returns value of 1.

    :param pageid: pageID of a wikipedia page
    :rtype: double
    :return: priority value
    """
    return 1


def _get_user_priority(userid):
    """
    Generate priority value for a given User ID.
    At present only returns value of 1.

    :param user: username of a wikipedia page
    :rtype: double
    :return: priority value
    """
    return 1


def _analysis_lock_status(page_id=None, user_id=None, analysis_type=None):
    """
    This is a utility function called by other DB manipulation functions.
    For an entry in analysis table, it checks the presence and lock status of that entry

    It first queries the analysis table with given pageID and analysis type.
    Using these two it retrieves lock status of entry.

    :param page_id: Page ID of the page under concern
    :param analysis_type: Analysis type ID of concerned analysis
    :return:
    """

    ret_dict = {}  # Initialize return dictionary

    # Check if requested for a page
    if page_id is not None:

        # Query the database for page ID and analysis type
        query = (db.page_analysis.analysis_type == analysis_type) & (db.page_analysis.pageid == page_id)
        analysis = db(query).select(db.page_analysis.ALL)
        first_analysis = analysis.first()

    # Check if requested for a user
    elif user_id is not None:

        # Query the database for user ID and analysis type
        query = (db.user_analysis.analysis_type == analysis_type) & (db.user_analysis.userid == user_id)
        analysis = db(query).select(db.user_analysis.ALL)
        first_analysis = analysis.first()

    else:
        return dict(status="ERROR", value="Both page and user are None")

    # Check if it is not none to check presence of an entry
    if first_analysis is not None:
        if len(analysis) > 1:
            # If more than one entry found, return an error specifying a conflict in database entries
            ret_dict['status'] = "ERROR"
            ret_dict['value'] = "More than one entry exists"
        else:
            # Otherwise extract the entry and convert to dict
            first_analysis = first_analysis.as_dict()

            # Get worker ID
            worker_id = first_analysis.get('worker_id', "0")

            if worker_id is None:
                # If worker_id is None then the analysis is free and available for update
                ret_dict['status'] = "OPEN"
                ret_dict['value'] = "Page-Analysis pair is open for creation/assignment"
            else:
                # Else the page is locked and can't be altered
                ret_dict['status'] = "LOCKED"
                ret_dict['value'] = "Page-Analysis pair is locked an cannot be altered"

    else:
        # No entry exists. Therefore, no lock exists. New entry can be created.
        ret_dict['status'] = "NEW"
        ret_dict['value'] = "Analysis record doesn't exist. Needs to be created before assignment"

    return ret_dict


def _create_page_analysis_response(analysis_dict=None, worker_id=None, work_start_date=None):
    """
    This utility function is called from assign controller.
    When the controller assigns an analysis, it needs an organized
    dict to return in the resulting json.
    That dict is built here in this function.

    It uses page and analysis type information from respective tables.
    It uses the three arguments provided for information on analysis

    :param analysis_dict: Dict containing DB entry for analysis
    :param worker_id: Worker ID generated for this assignment
    :param work_start_date: Time for assignment
    :return: Dict with organized information
    """

    base_dict = analysis_dict

    # Get page information from DB
    page = db(db.wikipages.pageid == analysis_dict['pageid']).select(db.wikipages.ALL).first()
    page = page.as_dict()
    base_dict.pop('pageid')

    # Build the page dict
    page.pop('id')
    page.pop('last_known_rev')

    base_dict['page'] = page

    # Get analysis_type information from DB
    analysis_type = db(db.analysis_type.id == analysis_dict['analysis_type']).select(db.analysis_type.ALL).first()
    analysis_type = analysis_type.as_dict()
    base_dict.pop('analysis_type')

    # Build the analysis_type dict
    analysis_type.pop('id')  # Removing DB id from entry
    base_dict['analysis'] = analysis_type

    # Build the remaining main_dict elements
    base_dict['priority'] = analysis_dict['priority']
    base_dict['worker_id'] = worker_id
    base_dict['work_start_date'] = work_start_date

    return base_dict


def _create_user_analysis_response(analysis_dict=None, worker_id=None, work_start_date=None):
    """
    This utility function is called from assign controller.
    When the controller assigns an analysis, it needs an organized
    dict to return in the resulting json.
    That dict is built here in this function.

    It uses user and analysis type information from respective tables.
    It uses the three arguments provided for information on analysis

    :param analysis_dict: Dict containing DB entry for analysis
    :param worker_id: Worker ID generated for this assignment
    :param work_start_date: Time for assignment
    :return: Dict with organized information
    """

    base_dict = analysis_dict

    # Get page information from DB
    user = db(db.wikiusers.id == analysis_dict['userid']).select(db.wikiusers.ALL).first()
    user = user.as_dict()
    #base_dict.pop('pageid')
    pprint(user)

    # Build the page dict
    user.pop('id')
    user.pop('last_known_rev')

    base_dict['user'] = user

    pprint(base_dict)

    # Get analysis_type information from DB
    analysis_type = db(db.analysis_type.id == analysis_dict['analysis_type']).select(db.analysis_type.ALL).first()
    analysis_type = analysis_type.as_dict()
    base_dict.pop('analysis_type')

    # Build the analysis_type dict
    analysis_type.pop('id')  # Removing DB id from entry
    base_dict['analysis'] = analysis_type

    # Build the remaining main_dict elements
    base_dict['priority'] = analysis_dict['priority']
    base_dict['worker_id'] = worker_id
    base_dict['work_start_date'] = work_start_date

    print "____________________________________"
    pprint(base_dict)
    return base_dict


def _get_revisions(pageid=None, base_revision=None, chunk_size=CHUNK_SIZE, continuous=False):
    """

    :param pageid:
    :return:
    """

    w = WikiFetch()
    revisions = w.fetch_revisions_for_page(pageid=pageid,
                                           start_rev=base_revision,
                                           chunk_size=chunk_size,
                                           continuous=continuous)
    print "Length of revisions at this level {}".format(len(revisions))

    return revisions


def _get_user_contributions(user=None, last_timestamp=None, continuous=False):
    """

    :param user:
    :param last_timestamp:
    :param continuous:
    :return:
    """
    w = WikiFetch()
    contributions = w.get_user_contributions(username=user,
                                             start_time=last_timestamp)
    print "Length of contributions at this level {}".format(len(contributions))

    return contributions



@request.restful()
def get_user_contribs():
    response.view = 'generic.' + request.extension

    def GET(*args, **vars):
        user = vars['user']

        return locals()

    return locals()


def _write_to_ndb(model, pageid, revision):
    """

    :param model:
    :param pageid:
    :param revision:
    :return:
    """
    # TODO: Convert into a better structure and remove if-else
    revid = revision['revid']

    format = "%Y-%m-%dT%H:%M:%SZ"

    if model == "revision_original":
        entry = Revision(id=str(revid),
                         revision_id=int(revid),
                         name=str(revid),
                         pageid=int(pageid),
                         userid=str(revision['userid']),
                         username=revision['user'],
                         revision_date=datetime.strptime(revision['timestamp'], format), )

        entry.put()
        return entry

    elif model == "trust":
        entry = RevisionTrust(id=str(revid),
                              revision_id=int(revid),
                              name=str(revid),
                              pageid=int(pageid),
                              userid=str(revision['userid']),
                              username=revision['user'],
                              revision_date=datetime.strptime(revision['timestamp'], format), )
        entry.put()
        print entry
        return entry


def _put_revisions_in_storage(pageid=None, bucket_name=None, folder_name=None, revisions=None, storage_meta=None,
                              ndb_entry=None):
    """

    :param revisions:
    :return:
    """
    g = GoogleConnect()

    for i, v in enumerate(revisions):
        revid = v['revid']
        filename = str(revid) + ".json"
        try:
            g.write_to_bucket(bucket_name=bucket_name,
                              folder_name=folder_name,
                              file_to_write=filename,
                              storage_meta=storage_meta,
                              content=json.dumps(obj=v))
            # print ("Written to bucket")

        except Exception, e:
            print "Exception while writing to bucket is: {}".format(str(e))
            # return e
            raise HTTP(500)

        try:
            # Make meta-data entry into NDB


            entry = _write_to_ndb(model=ndb_entry,
                                  pageid=pageid,
                                  revision=v)

        except Exception, er:
            print "Error is {}".format(str(er))
            # print er
            # return er
            raise HTTP(500)
            # print "Count - {}".format(i)


def index():
    """
    Shows open analysis requirements. Index only for the web page.
    No relation with server functions in particular

    :return: Return local variables to the view where they can be printed
    """

    query = (db.page_analysis.worker_id == None)
    items = db(query).select(db.page_analysis.ALL)
    if items is not None:
        items = items.as_dict()
    else:
        items = {}

    # generate()

    return locals()


def create_page_analysis(pageid=None, analysis_type=None):
    """
    Create Page Analysis is called through the generate function for
    each analysis type per page with change.

    This function checks presence and status of an analysis in the 'analysis' table,
    and then makes decision for a new analysis entry:
    - If there is no analysis-page entry in the table, then it creates a new entry.
    - If there is an entry but it is locked (status="active" and worker_id, work_start_date are not None),
      then decline creation of a new analysis.
    - If there is an entry, and it isn't locked, then make it active

    :param pageid: Wikipedia Page ID of the page with change
    :param analysis_type: Analysis type used to create an analysis need. Defaults to global Default
    :return: dict holding status and value. If successful, value is DB entry ID for analysis
    """

    ret_dict = {}  # Initialize return dictionary

    lock_status = _analysis_lock_status(page_id=pageid, analysis_type=analysis_type)

    if lock_status['status'] in ["NEW", "OPEN"]:
        # If it's a new or open analysis, then make it active
        # Create an entry in Analysis table
        query = (db.page_analysis.pageid == pageid) & (db.page_analysis.analysis_type == analysis_type)
        try:
            analysis_id = db.page_analysis.update_or_insert(query,
                                                            analysis_type=analysis_type,
                                                            pageid=pageid,
                                                            worker_id=None,
                                                            work_start_date=None,
                                                            status="active",
                                                            priority=_get_page_priority(pageid=pageid)
                                                            # Priority of page
                                                            )
            # If an entry has been created or updated, return success with DB entry ID
            ret_dict['status'] = "SUCCESS"
            ret_dict['value'] = analysis_id

        except Exception as e:
            ret_dict['status'] = "ERROR"
            ret_dict['value'] = e
    else:
        # Analysis entry cannot be created.
        ret_dict = lock_status

    # Return the dict holding status and value
    return ret_dict


def create_user_analysis(user_id=None, analysis_type=None):
    """
    Create User Analysis is called through the generate function for
    each analysis type per user with change.

    This function checks presence and status of an analysis in the 'analysis' table,
    and then makes decision for a new analysis entry:
    - If there is no analysis-user entry in the table, then it creates a new entry.
    - If there is an entry but it is locked (status="active" and worker_id, work_start_date are not None),
      then decline creation of a new analysis.
    - If there is an entry, and it isn't locked, then make it active

    :param user_id: Wikipedia Username of the page with change
    :param analysis_type: Analysis type used to create an analysis need. Defaults to global Default
    :return: dict holding status and value. If successful, value is DB entry ID for analysis
    """

    ret_dict = {}  # Initialize return dictionary

    lock_status = _analysis_lock_status(user_id=user_id, analysis_type=analysis_type)

    if lock_status['status'] in ["NEW", "OPEN"]:

        # If it's a new or open analysis, then make it active
        # Create an entry in Analysis table

        query = (db.user_analysis.userid == user_id) & (db.user_analysis.analysis_type == analysis_type)
        try:
            analysis_id = db.user_analysis.update_or_insert(query,
                                                            analysis_type=analysis_type,
                                                            userid=user_id,
                                                            worker_id=None,
                                                            work_start_date=None,
                                                            status="active",
                                                            priority=_get_user_priority(userid=user_id)
                                                            # Priority of user
                                                            )
            # If an entry has been created or updated, return success with DB entry ID
            ret_dict['status'] = "SUCCESS"
            ret_dict['value'] = analysis_id

        except Exception as e:
            ret_dict['status'] = "ERROR"
            ret_dict['value'] = e
    else:
        # Analysis entry cannot be created.
        ret_dict = lock_status

    # Return the dict holding status and value
    return ret_dict


def generate():
    """
    Generate function is called through a job continuously.

    This function polls Wikipedia for recent changes and then creates analysis entry
    for those pages in analysis table (per analysis).
        - This entry will now stay in the table. If the entry was already there,
        it has its last_annotated revision updated in it.
        - Otherwise, value of 0 is provided to the last_annotated revision column and
        this page needs to get updated from first revision.
        - Status of an entry in analysis table is set to active indicating that it
        needs work to be performed
        - An entry now has the page id, a last known revision for reference,
        a last_annotated id which is either already there or is 0 for new, and analysis type

    :return: A dict holding information of pages with recent changes
    """

    generated_pa_entries = set()  # Initializing set of page analysis entries generated in one call
    generated_ua_entries = set()  # Initializing set of user analysis entries generated in one call

    # Get pages with changes
    # Comes in as a dict of pages with recent changes
    pages_with_changes = WikiFetch.get_recent_changes()

    pprint(pages_with_changes)
    # Set these pages open for each analysis
    # Create or update analysis entry in table for analysis
    # Iterating over all new pages with changes
    for k, v in pages_with_changes.iteritems():
        # Extract page ID, title and latest revision from Wikipedia.
        # Language not available in this call
        pageid = k
        title = v['title']
        last_known_rev = v['last_known_rev']

        user = v['user']
        userid = v['userid']

        # Update page table with this page's entry.
        query = (db.wikipages.pageid == pageid)
        page_id = db.wikipages.update_or_insert(query,
                                                pageid=pageid,
                                                last_known_rev=last_known_rev,
                                                title=title)

        # Update user table with this user's entry
        query = (db.wikiusers.username == user)
        user_id = db.wikiusers.update_or_insert(query,
                                                username=user,
                                                last_known_rev=last_known_rev,
                                                last_edited_page=pageid)

        # Get available analysis_types
        analysis_types = _get_analysis_type_from_db()
        print(analysis_types)
        # For each available analysis, make an analysis requirement
        for analysis, info in analysis_types.iteritems():

            # Check if analysis is for page
            if info[1]:
                # Call the create analysis function for writing entry in the DB.
                page_analysis_entry = create_page_analysis(pageid=pageid, analysis_type=analysis)
                # Call the create analysis function for writing entry in the DB.
                # analysis_entry = create_user_analysis(username=username, analysis_type=analysis)

                print page_analysis_entry
                if page_analysis_entry['status'] == "SUCCESS":
                    # If an entry has been created, add it to the set of generated entries
                    generated_pa_entries.add(page_analysis_entry['value'])
                else:
                    # TODO: Based on response, log the error or success of entries.
                    pass

            # If not for page, then it is for user.
            else:
                logging.info("This should be a user analysis")

                # Call the create analysis function for writing entry in the DB.
                user_analysis_entry = create_user_analysis(user_id=user_id, analysis_type=analysis)

                print user_analysis_entry
                if user_analysis_entry['status'] == "SUCCESS":
                    # If an entry has been created, add it to the set of generated entries
                    generated_ua_entries.add(user_analysis_entry['value'])
                else:
                    # TODO: Based on response, log the error or success of entries.
                    pass

    return locals()


@request.restful()
def assign():
    """
    This function hosts a RESTful GET call.

    A request to this function assigns an open analysis to requester.
    Upon assignment, the function updates analysis entry in the table.

    This function then creates a dictionary containing
    entire analysis job data. A GET request to the function assigns
    a new analysis to the worker and then returns
    this dict which can be fetched as both JSON and XML.

    :return:
    """
    response.view = 'generic.' + request.extension

    def GET(*args, **vars):

        # Basic authentication check using a secret
        # TODO: Change to header based authentication
        try:
            secret = vars['secret']
            if secret != MYSECRET:
                raise HTTP(400)
        except KeyError, e:
            print str(e)
            raise HTTP(400)

        type = vars.get('type', None)
        continuous = vars.get('continuous', False)

        if type:
            if type == "page":
                # Select an open task for assignment
                query = (db.page_analysis.status == "active") & (db.page_analysis.worker_id == None)
                open_analysis = db(query).select(db.page_analysis.ALL).first()  # First open analysis

            elif type == "user":
                # Select an open task for assignment
                query = (db.user_analysis.status == "active") & (db.user_analysis.worker_id == None)
                open_analysis = db(query).select(db.user_analysis.ALL).first()  # First open analysis
            else:
                raise HTTP(403, "Invalid type requested")

        else:
            raise HTTP(403, "Type not provided")

        if open_analysis is None:
            raise HTTP(404)

        # Get an ID to assign the worker
        worker_id = _generate_worker_id()

        # Set assignment date to now
        work_start_date = datetime.utcnow()

        # Update database entry and generate return dict
        open_analysis.update_record(worker_id=worker_id,
                                    work_start_date=work_start_date)
        if type == "page":
            response_dict = _create_page_analysis_response(open_analysis.as_dict(),
                                                      worker_id,  # Not updated in open_analysis
                                                      work_start_date  # Not updated in open_analysis
                                                      )
        elif type == "user":
            response_dict = _create_user_analysis_response(open_analysis.as_dict(),
                                                      worker_id,  # Not updated in open_analysis
                                                      work_start_date  # Not updated in open_analysis
                                                      )
            pprint(response_dict)


        """
        if vars.has_key('prefetch') and vars['prefetch']:
            # Get the revisions from Wikipedia
            # Put revisions in GCS
            # Put revision metadata in NDB datastore

            pageid = response_dict['page']['pageid']
            revisions = _get_revisions(pageid=pageid,
                           base_revision=response_dict['last_annotated'],
                           continuous=continuous)
            storage_result = _put_revisions_in_storage(pageid=pageid,
                                                       bucket_name="revision_original",
                                                       revisions=revisions)
        """
        pprint(response_dict)
        return response_dict

    return locals()


@request.restful()
def get_revisions():
    """

    :return:
    """
    response.view = 'generic.' + request.extension

    def GET(*args, **vars):

        # Basic authentication check using a secret
        # TODO: Change to header based authentication
        try:
            secret = vars['secret']
            if secret != MYSECRET:
                raise HTTP(400)
        except KeyError, e:
            # print e
            raise HTTP(400)

        if vars.has_key('continuous'):
            continuous = bool(vars['continuous'])
            # print continuous
            # print(type(continuous))
        else:
            continuous = False

            # try:
            # Get the revisions from Wikipedia
            # Put revisions in GCS
            # Put revision metadata in NDB datastore

        if vars.has_key('pageid'):
            pageid = vars['pageid']
        else:
            raise HTTP('403', 'Page ID not provided')

        if vars.has_key('base_revision'):
            base_revision = vars['base_revision']
        else:
            raise HTTP('403', "base revision not provided")

        try:
            print pageid
            print base_revision
            revisions = _get_revisions(pageid=pageid,
                                       base_revision=base_revision,
                                       continuous=continuous)
            print "Success till here"
        except Exception, e:
            print "Error in getting revisions"
            print(e)
            raise HTTP('403', 'Problem in getting revisions')

        try:

            storage_result = _put_revisions_in_storage(pageid=pageid,
                                                       bucket_name="revisions",
                                                       folder_name="original",
                                                       revisions=revisions,
                                                       ndb_entry="revision_original",
                                                       storage_meta=ALGO_META['revision_original'])
            print "Should be done"

            print(type(revisions))
            return dict(revisions=revisions)
        except Exception, e:
            print "Error at exception in get_revisions"
            # print(e)
            # raise HTTP(400)
            # raise HTTP(500)

        print "No.of revisions {}".format(len(revisions))

        # return revisions

    return locals()


@request.restful()
def get_user_contributions():
    """

    :return:
    """
    response.view = 'generic.' + request.extension

    def GET(*args, **vars):

        # Basic authentication check using a secret
        # TODO: Change to header based authentication
        try:
            secret = vars['secret']
            if secret != MYSECRET:
                raise HTTP(400)
        except KeyError, e:
            # print e
            raise HTTP(400)

        continuous = vars.get('continuous', False)

            # try:
            # Get the revisions from Wikipedia
            # Put revisions in GCS
            # Put revision metadata in NDB datastore

        if vars.has_key('user'):
            user = vars['user']
        else:
            raise HTTP('403', 'Page ID not provided')

        if vars.has_key('last_timestamp'):
            last_timestamp = vars['last_timestamp']
        else:
            raise HTTP('403', "last timestamp not provided")

        try:
            contributions = _get_user_contributions(user=user,
                                       last_timestamp=last_timestamp)
            print "Success till here"
        except Exception, e:
            print "Error in getting user contributions"
            print(e)
            raise HTTP('403', 'Problem in getting user contributions')


        print "No.of contributions {}".format(len(contributions))

        return contributions

    return locals()


@request.restful()
def complete():
    """
    This function is called through a POST request.

    A request to this function contains work performed by a client on
    an assigned analysis.
    Client's submission data is inserted into the DB here to update
    analysis's status.

    Check is performed here with submitted last revision and current revision.
    With this check the function decides change in status of analysis.

    Input of form:
    {
        'analysis_id':"",
        'pageid':"",
        'worker_id':"",
        'last_annotated':"",
        'start_time':"",
        'end_time':""
    }
    :param analysis_entry:
    :param comments:
    :return:
    """
    response.view = 'generic.' + request.extension

    def POST(*args, **vars):

        # Extract DB entry ID and last_annotated from vars

        entry_id = vars['id']
        last_annotated = vars['last_annotated']
        pageid = vars['page']['pageid']
        analysis_type = vars['analysis']['name']
        print analysis_type
        print last_annotated

        last_annotated = int(last_annotated)
        # Validate submission by checking worker ID
        entry = db(db.page_analysis.id == entry_id).select().first()
        if entry.worker_id != vars['worker_id']:
            raise HTTP(403, "Validation failed")

        # Put the result entries into storage and meta data into NDB tables
        revisions = vars['revisions']
        for i, v in enumerate(revisions):

            try:
                bucket_name = "revisions/" + analysis_type
                ndb_entry = "revision_" + analysis_type
                storage_result = _put_revisions_in_storage(pageid=pageid,
                                                           bucket_name=bucket_name,
                                                           revisions=revisions,
                                                           ndb_entry=str(analysis_type))

            except Exception, e:
                print "Error at exception in get_revisions"
                # print(e)
                # raise HTTP(400)
                raise HTTP(500)

        # Get page info for the page ID containing latest revision
        WIKI_PARAMS['page_info']["pageids"] = pageid
        result = _get(url=WIKI_BASE_URL, values=WIKI_PARAMS['page_info'])

        if result['query'] != 'Error':
            last_known_rev = result["query"]["pages"][pageid]["lastrevid"]
            print "Last known Revision is {}".format(last_known_rev)
            print "Last annotated revision is {}".format(last_annotated)

            if last_annotated == last_known_rev:

                # Close the analysis. Remove entry from DB
                entry = db(db.page_analysis.id == entry_id).select().first()
                entry.update_record(worker_id=None,
                                    work_start_date=None,
                                    last_annotated=last_annotated,
                                    status="inactive")
            else:
                # Reopen the analysis. Set worker ID and start date to None
                entry = db(db.page_analysis.id == entry_id).select().first()
                entry.update_record(worker_id=None,
                                    work_start_date=None,
                                    last_annotated=last_annotated,
                                    status="active")

        return (dict(status="done"))

    return locals()


