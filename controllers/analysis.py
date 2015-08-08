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
from pprint import pprint

from wikipedia import WikiFetch, WIKI_PARAMS, WIKI_BASE_URL
from google_connect import GoogleConnect
from datetime import datetime
import random

__author__ = 'rakshit'

MYSECRET = "secretcode"


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
        ret_dict[entry.id] = entry.name

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


def _analysis_lock_status(pageid, analysis_type):
    """
    This is a utility function called by other DB manipulation functions.
    For an entry in analysis table, it checks the presence and lock status of that entry

    It first queries the analysis table with given pageID and analysis type.
    Using these two it retrieves lock status of entry.

    :param pageid: Page ID of the page under concern
    :param analysis_type: Analysis type ID of concerned analysis
    :return:
    """

    # Query the database for page ID and analysis type
    query = (db.analysis.analysis_type == analysis_type) & (db.analysis.pageid == pageid)
    analysis = db(query).select(db.analysis.ALL)
    first_analysis = analysis.first()

    ret_dict = {}  # Initialize return dictionary

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
            worker_id = first_analysis['worker_id']

            if worker_id is None:
                # If worker_id is None then the analysis is free and available for update
                ret_dict['status'] = "OPEN"
                ret_dict['value'] = "Page-Analysis pair is open for creation/assignment"
                pass
            else:
                # Else the page is locked and can't be altered
                ret_dict['status'] = "LOCKED"
                ret_dict['value'] = "Page-Analysis pair is locked an cannot be altered"
                pass

    else:
        # No entry exists. Therefore, no lock exists. New entry can be created.
        ret_dict['status'] = "NEW"
        ret_dict['value'] = "Page-Analysis pair doesn't exist. Needs to be created before assignment"

    return ret_dict


def _create_analysis_response(analysis_dict=None, worker_id=None, work_start_date=None):
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


def _get_revisions(pageid=None, base_revision=None, chunk_size=20, continuous=False):
    """

    :param pageid:
    :return:
    """

    w = WikiFetch()
    revisions = w.fetch_revisions_for_page(pageid=pageid,
                                           start_rev=base_revision,
                                           chunk_size=chunk_size,
                                           continuous=continuous)

    return revisions


def _put_revisions_in_storage(pageid = None, bucket_name = None, revisions = None):
    """

    :param revisions:
    :return:
    """
    g = GoogleConnect()

    for i in revisions:
        revid = i['revid']

        filename = str(revid) + ".json"
        try:
            g.write_to_bucket(bucket_name=bucket_name,
                          file_to_write=filename,
                          content = json.dumps(obj=i))
            print ("Written to bucket")



        except Exception, e:
            print "Exception while writing to bucket is: {}".format(e)
            return e

        try:
            # Make meta-data entry into NDB
            format = "%Y-%m-%dT%H:%M:%SZ"

            entry = Revision(id = str(revid),
                             revision_id = int(revid),
                             name = str(revid),
                             pageid = int(pageid),
                             userid=str(i['userid']),
                             username = i['user'],
                             revision_date = datetime.strptime(i['timestamp'],format))

            entry.put()
        except Exception, er:
            print er
            return er



def index():
    """
    Shows open analysis requirements. Index only for the web page.
    No relation with server functions in particular

    :return: Return local variables to the view where they can be printed
    """

    query = (db.analysis.worker_id == None)
    items = db(query).select(db.analysis.ALL)
    if items is not None:
        items = items.as_dict()
    else:
        items = {}

    # generate()

    return locals()


def create_analysis(pageid=None, analysis_type=None):
    """
    Create Analysis is called through the generate function for
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

    lock_status = _analysis_lock_status(pageid=pageid, analysis_type=analysis_type)

    if lock_status['status'] in ["NEW", "OPEN"]:
        # If it's a new or open analysis, then make it active
        # Create an entry in Analysis table
        query = (db.analysis.pageid == pageid) & (db.analysis.analysis_type == analysis_type)
        try:
            analysis_id = db.analysis.update_or_insert(query,
                                                       analysis_type=analysis_type,
                                                       pageid=pageid,
                                                       worker_id=None,
                                                       work_start_date=None,
                                                       status="active",
                                                       priority=_get_page_priority(pageid=pageid)  # Priority of page
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

    generated_entries = set()  # Initializing set of analysis entries generated in one call

    # Get pages with changes
    # Comes in as a dict of pages with recent changes
    pages_with_changes = WikiFetch.get_recent_changes()

    # Set these pages open for each analysis
    # Create or update analysis entry in table for analysis
    # Iterating over all new pages with changes
    for k, v in pages_with_changes.iteritems():
        # Extract page ID, title and latest revision from Wikipedia.
        # Language not available in this call
        pageid = k
        title = v['title']
        last_known_rev = v['last_known_rev']

        # Update page table with this page's entry.
        query = (db.wikipages.pageid == pageid)
        page_id = db.wikipages.update_or_insert(query,
                                                pageid=pageid,
                                                last_known_rev=last_known_rev,
                                                title=title)

        # Get available analysis_types
        analysis_types = _get_analysis_type_from_db()
        print(analysis_types)
        # For each available analysis, make an analysis requirement
        for analysis in analysis_types.keys():

            # Call the create analysis function for writing entry in the DB.
            analysis_entry = create_analysis(pageid=pageid, analysis_type=analysis)
            print analysis_entry
            if analysis_entry['status'] == "SUCCESS":
                # If an entry has been created, add it to the set of generated entries
                generated_entries.add(analysis_entry['value'])
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
            print e
            raise HTTP(400)

        if vars.has_key('continuous'):
            continuous = vars['continuous']
        else:
            continuous = False

        # Select an open task for assignment
        query = (db.analysis.status == "active") & (db.analysis.worker_id == None)
        open_analysis = db(query).select(db.analysis.ALL).first()  # First open analysis

        print(open_analysis is None)

        if open_analysis is None:
            raise HTTP(404)

        # Get an ID to assign the worker
        worker_id = _generate_worker_id()

        # Set assignment date to now
        work_start_date = datetime.utcnow()

        # Update database entry and generate return dict
        open_analysis.update_record(worker_id=worker_id,
                                    work_start_date=work_start_date)
        response_dict = _create_analysis_response(open_analysis.as_dict(),
                                                  worker_id,  # Not updated in open_analysis
                                                  work_start_date  # Not updated in open_analysis
                                                  )

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
            print e
            raise HTTP(400)

        if vars.has_key('continuous'):
            continuous = vars['continuous']
        else:
            continuous = False

        try:
            # Get the revisions from Wikipedia
            # Put revisions in GCS
            # Put revision metadata in NDB datastore

            pageid = vars['pageid']
            base_revision = vars['base_revision']
            continuous = bool(vars['continuous']) if not None else False

            revisions = _get_revisions(pageid=pageid,
                           base_revision=base_revision,
                           continuous=continuous)
            storage_result = _put_revisions_in_storage(pageid=pageid,
                                                       bucket_name="revision_original",
                                                       revisions=revisions)
        except:
            raise HTTP(500)

        return revisions

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
        entry_id = vars['analysis_id']
        last_annotated = vars['last_annotated']
        pageid = vars['pageid']

        # Validate submission by checking worker ID
        entry = db(db.analysis.id == entry_id).select().first()
        if entry.worker_id != vars['worker_id']:
            raise HTTP(403, "Validation failed")

        # Get page info for the page ID containing latest revision
        WIKI_PARAMS['page_info']["pageids"] = pageid
        result = WikiFetch._get(url=WIKI_BASE_URL, values=WIKI_PARAMS['page_info'])

        if result['query'] != 'Error':
            last_known_rev = result["query"]["pages"][pageid]["lastrevid"]

            if last_annotated == last_known_rev:
                # Close the analysis. Remove entry from DB
                query = (db.analysis.id == entry_id)
                db(query).update(worker_id=None,
                                 work_start_date=None,
                                 last_annotated=last_annotated,
                                 status="inactive")
            else:
                # Reopen the analysis. Set worker ID and start date to None
                query = (db.analysis.id == entry_id)
                db(query).update(worker_id=None,
                                 work_start_date=None,
                                 last_annotated=last_annotated,
                                 status="active")

    return locals()
