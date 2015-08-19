import json

import urllib
import urllib2
import cloudstorage as gcs
from http_requests import _post
from oauth_handler import get_access_token
from credentials import CLIENT_ID, CLIENT_SECRET

__author__ = 'rakshit'



class GoogleConnect:
    def __init__(self):
        my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                                  max_delay=5.0,
                                                  backoff_factor=2,
                                                  max_retry_period=15)

        gcs.set_default_retry_params(my_default_retry_params)
        pass

    def write_to_bucket(self, bucket_name=None, folder_name = None, file_to_write=None, content = None, storage_meta= None,
                        content_type='application/json'):
        """


        :type content_type: object
        :param bucket_name:
        :param file_to_write:
        :return:
        """
        bucket_name = str(bucket_name)
        bucket = "/" + bucket_name
        if folder_name:
            bucket = bucket + "/" + folder_name
        filename = bucket + "/" + file_to_write


        #print filename
        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
        try:

            gcs_file = gcs.open(filename,
                                'w',
                                content_type=content_type,
                                options=storage_meta,
                                retry_params=write_retry_params)


        except Exception, e:
            print e
            raise Exception


        #print gcs_file
        if content:
            gcs_file.write(data=content)
        else:
            gcs_file.write('test text')
        print gcs_file
        try:
            print gcs_file.key()
        except Exception, e:
            print e
        gcs_file.close()
        """

        print "In write to bucket"

        url = "https://www.googleapis.com/upload/storage/v1/b/" +  bucket_name + "/o"
        #values = dict(uploadType="media", name=filename, media_body=content)
        url = url+ '?' + "uploadType=media&name="+ filename


        tokens = get_access_token(CLIENT_ID=CLIENT_ID, CLIENT_SECRET=CLIENT_SECRET)
        print tokens
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']

        headers = { 'content-type' : content_type }

        data = dict(content=str(content), access_token=access_token)
        #content = json.dumps(content)
        print "Type of content is {}".format(type(content))
        gcs_file = _post(url=url,
                         values=data,
                         headers=headers)
        print gcs_file

        """

    def read_from_bucket(self, bucket_name=None, file_to_write=None):
        """

        :param bucket_name:
        :param file_to_write:
        :return:
        """
        bucket = "/" + bucket_name
        filename = bucket + "/" + file_to_write

        gcs_file = gcs.open(filename)
        content = gcs_file.readline()
        gcs_file.close()
        #print(content)

        return content


