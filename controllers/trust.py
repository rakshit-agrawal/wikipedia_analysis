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
            'params':[
                        {
                            'property':"",
                            'values':""
                        }
                    ]
        }

        :param args: Arguments submitted with the GET request
        :param vars: Variables sent with the GET request
        :return: Dictionary with processed propery values
        :rtype: dict
        """

        values = vars["values"].split("|")
        user_dict = {}
        for i, v in enumerate(values):
            user_dict[v] = _get_user_reputation(user=v)

        return user_dict

    return locals()
