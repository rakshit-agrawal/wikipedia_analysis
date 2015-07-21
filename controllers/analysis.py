import os
import pickle
from wikipedia import WikiFetch, WIKI_PARAMS, WIKI_BASE_URL
from datetime import datetime
import random

__author__ = 'rakshit'

ANALYSIS_LIST = ["trust"]
DEFAULT_ANALYSIS = "trust"

def _generate_worker_id():
    """
    Generate a random worker ID
    :return:
    """
    val = random.getrandbits(64)

    return str(val)


def _get_page_priority(pageid):
    return 1


def _analysis_lock_status(pageid, analysis_type):
    """
    Check lock status of a page and analysis.
    Page is locked if it has a worker ID assigned to it.

    :param pageid:
    :param analysis_type:
    :return:
    """
    query = (db.analysis.analysis_type == analysis_type) & (db.analysis.pageid == pageid)
    analysis = db(query).select(db.analysis.ALL).first()
    if analysis is not None:
        analysis = analysis.as_dict()
    else:
        analysis = dict(worker_id="DOES_NOT_EXIST")

    worker_id = analysis['worker_id']

    if worker_id is None:
        # Case for assign
        ret_val = False  # Unlocked
    elif worker_id == "DOES_NOT_EXIST":
        # Case for open
        ret_val = False  # Unlocked because entry doesn't exist
    else:
        ret_val = True # Locked

    return ret_val


def _get_analysis_dict(analysis_type):
    """
    Create a dict for analysis type and its
    associated data

    :param analysis_type:
    :return:
    """
    analysis_dict = dict()

    analysis_dict['type'] = analysis_type
    analysis_dict['coefficients'] = {}

    return analysis_dict

def _create_analysis_response(analysis_dict):
    """
    Create a JSON for the analysis data provided

    :param id:
    :param pageid:
    :param base_revision:
    :param target_revision:
    :param create_date:
    :param priority:
    :param status:
    :param assign_date:
    :return:
    """

    base_dict = dict()
    dict_page = base_dict['page'] = dict()

    dict_page['pageid'] = analysis_dict['pageid']
    dict_page['base_revision'] = analysis_dict['last_annotated']

    base_dict['priority'] = analysis_dict['priority']
    base_dict['worker_id'] = analysis_dict['worker_id']

    base_dict['work_start_date'] = analysis_dict['work_start_date']

    dict_analysis = base_dict['analysis'] = dict()
    dict_analysis = _get_analysis_dict(analysis_type=analysis_dict['analysis_type'])

    return base_dict

def _generate_error_response(error=100):
    base_dict = dict()

    base_dict['status'] = "Error"
    base_dict['code'] = error
    #base_dict["error"] = ERROR_CODES[error]

    return base_dict


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


def create_analysis(pageid=None, analysis_type=DEFAULT_ANALYSIS):
    """
    Create Analysis is called through the generate function for
    each analysis type per page with change.

    This function checks presence and status of an analysis in the 'analysis' table,
    and then makes decision for a new analysis entry:
    - If there is no analysis-page entry in the table, then it creates a new entry.
    - If there is an entry but it is locked (status="active" and worker_id, work_start_date are not None),
      then decline creation of a new analysis.
    - If there is an entry, and it isn't locked, then make it active

    :param pageid: PageID of the page with change
    :param analysis_type: Analysis type used to create an analysis need. Defaults to global Default
    :return: Analysis ID of new entry, an error if locked
    """

    if not _analysis_lock_status(pageid = pageid, analysis_type=analysis_type):
        # Create an entry in Analysis table
        query = (db.analysis.pageid==pageid) & (db.analysis.analysis_type==analysis_type)
        analysis_id = db.analysis.update_or_insert(query,
                                                   analysis_type=analysis_type,
                                                   pageid=pageid,
                                                   worker_id=None,
                                                   work_start_date=None,
                                                   status="active",
                                                   priority = _get_page_priority(pageid=pageid))
    else:
        analysis_id = None

    return analysis_id


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
    w = WikiFetch()  # Create a WikiFetch object for calling Wikipedia APIs

    # Get pages with changes
    # Comes in as a dict of pages with recent changes
    pages_with_changes = w.get_recent_changes()

    # Set the pages open for each analysis
    # Create or update analysis entry in table for analysis

    # Iterating over all new pages with changes
    for k,v in pages_with_changes.iteritems():
        pageid = k
        title = v['title']
        last_known_rev = v['last_known_rev']

        # Update page table with this page's entry.
        # TODO: Add entry in page table

        # For each available analysis, make an analysis requirement
        for analysis in ANALYSIS_LIST:
            # Call the create analysis function for writing entry in the DB.
            analysis_id = create_analysis(pageid=pageid,analysis_type=analysis)


    return locals()


def assign():
    """
    Assign analysis for a given page to a worker.
    Fetch all initial elements of an analysis and make its entry
    in the DB.

    :param pageid:
    :param analysis_type:
    :return:
    """

    if request.args and (len(request.args)>=2):
        pageid = request.args(0)
        analysis_type = request.args(1)
    
    else:
        raise HTTP(403, "Arguments not provided")
        

    # Get an ID to assign the worker
    worker_id = _generate_worker_id()
    work_start_date = datetime.utcnow()

    query = (db.analysis.analysis_type == analysis_type) & (db.analysis.pageid == pageid)
    analysis = db(query).select(db.analysis.ALL).first()

    if analysis is not None:
        analysis_dict = analysis.as_dict()
    else:
        analysis_dict = dict(worker_id="DOES_NOT_EXIST")

    if analysis_dict['worker_id'] is not None:
        # Locked
        response_dict = _generate_error_response(error=101)
    else:
        # Update the record with worker assignment
        analysis.update_record(worker_id=worker_id, work_start_date=work_start_date)
        response_dict = _create_analysis_response(analysis_dict)

    return response_dict


def close_analysis(analysis_entry=None, comments=None):
    """
    Check for analysis completion level and close it if done.
    For a given analysis for a page, check worker's last_annotated
    revision and check its current revision. If both are same,
    it can be closed. Otherwise keep it open

    :return:
    """
    w = WikiFetch()

    pageid = analysis_entry['pageid']
    last_annotated = analysis_entry['last_annotated']
    analysis_type = analysis_entry['analysis_type']

    # Get page info for the page ID containing latest revision
    WIKI_PARAMS['page_info']["pageids"] = pageid
    result = w._get(url=WIKI_BASE_URL, values=WIKI_PARAMS['page_info'])

    if result['query'] != 'Error':
        last_known_rev = result["query"]["pages"][pageid]["lastrevid"]

    if last_annotated == last_known_rev:
        # Close the analysis. Remove entry from DB
        query = (db.analysis.id == analysis_entry['id'])
        db(query).update(worker_id=None, work_start_date=None, last_annotated=last_annotated, status="inactive")
    else:
        # Reopen the analysis. Set worker ID and start date to None
        query = (db.analysis.id == analysis_entry['id'])
        db(query).update(worker_id=None, work_start_date=None, last_annotated=last_annotated, status="active")

    # Update analysis entry with last_annotated
