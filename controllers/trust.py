import json
import random

__author__ = 'rakshit'


def _get_user_reputation(user):
    return random.random()


@request.restful()
def get_meta():
    """

    :return:
    """
    response.view = 'generic.'+request.extension

    def GET(*args, **vars):
        """
        Vars contain the metadata request dictionary
        Structure:
        {
            'query': "meta",
            'analysis_type':"",
            'property':"",
            'values':"a|b|c"
        }

        :param args: Arguments submitted with the GET request
        :param vars: Variables sent with the GET request
        :return: Dictionary with processed property values
        :rtype: dict
        """

        values = vars["values"].split("|")
        user_dict = {}
        for i, v in enumerate(values):
            user_dict[v] = _get_user_reputation(user=v)

        return user_dict

    return locals()

"""
{
    'analysis_id':val,
    'analysis_type':val,
    'pageid':val,
    'last_annotated':val,
    'completion_time':val,
    'worker_id':val,
    'revisions': [
        {
            'revid':val,
            'rev_date':val,
            'userid':val,
            'username':val,
            'analysis_date':val,
            'overall_trust':val,
            'coeff':val,
            'annotated_text':"large text set"

        }
    ]


}
"""