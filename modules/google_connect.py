import os
import cloudstorage as gcs

__author__ = 'rakshit'


class GoogleConnect:
    def __init__(self):
        my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                                  max_delay=5.0,
                                                  backoff_factor=2,
                                                  max_retry_period=15)

        gcs.set_default_retry_params(my_default_retry_params)
        pass

    def write_to_bucket(self, bucket_name=None, file_to_write=None, content = None, storage_meta= None,
                        content_type='application/json'):
        """


        :type content_type: object
        :param bucket_name:
        :param file_to_write:
        :return:
        """
        bucket = "/" + bucket_name
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

        gcs_file.close()

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


