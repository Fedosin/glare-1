# Copyright 2017 Nokia
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Contains additional file utils that may be useful for upload hooks."""

import os
import tempfile
import zipfile

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils

from glare.common import store_api
from glare.objects.meta import fields as glare_fields

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def create_temporary_file(stream, suffix=''):
    """Create a temporary local file from a stream.

    :param stream: stream of bytes to be stored in a temporary file
    :param suffix: (optional) file name suffix
    """
    tfd, path = tempfile.mkstemp(suffix=suffix)
    while True:
        data = stream.read(100000)
        if data == '':  # end of file reached
            break
        os.write(tfd, data)
    tfile = os.fdopen(tfd)
    return tfile, path


def extract_zip_to_temporary_folder(tfile):
    """Create temporary folder and extract all file contents there.

    :param tfile: zip archive to be extracted
    """
    zip_ref = zipfile.ZipFile(tfile, 'r')
    tdir = tempfile.mkdtemp()
    zip_ref.extractall(tdir)
    zip_ref.close()
    return tdir


def upload_content_file(context, af, data, blob_dict, key_name,
                        content_type='application/octet-stream'):
    """Upload a file to a blob dictionary.

    :param context: user context
    :param af: artifact object
    :param data: bytes that need to be stored in the blob dictionary
    :param blob_dict: name of the blob_dictionary field
    :param key_name: name of key in the dictionary
    :param content_type: (optional) specifies mime type of uploading data
    """
    # create an an empty blob instance in db with 'saving' status
    blob = {'url': None, 'size': None, 'md5': None, 'sha1': None,
            'sha256': None, 'status': glare_fields.BlobFieldType.SAVING,
            'external': False, 'content_type': content_type}

    getattr(af, blob_dict)[key_name] = blob
    af = af.update_blob(context, af.id, blob_dict, getattr(af, blob_dict))

    blob_id = getattr(af, blob_dict)[key_name]['id']

    # try to perform blob uploading to storage backend
    try:
        default_store = af.get_default_store(context, af, blob_dict, key_name)
        location_uri, size, checksums = store_api.save_blob_to_store(
            blob_id, data, context, af.get_max_blob_size(blob_dict),
            default_store)
    except Exception:
        # if upload failed remove blob from db and storage
        with excutils.save_and_reraise_exception(logger=LOG):
            del getattr(af, blob_dict)[key_name]
            af = af.update_blob(context, af.id,
                                blob_dict, getattr(af, blob_dict))
    # update blob info and activate it
    blob.update({'url': location_uri,
                 'status': glare_fields.BlobFieldType.ACTIVE,
                 'size': size})
    blob.update(checksums)
    getattr(af, blob_dict)[key_name] = blob
    af.update_blob(context, af.id, blob_dict, getattr(af, blob_dict))
