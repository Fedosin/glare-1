# Copyright 2017 - Nokia Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import mock

from glare.common import exception as exc
from glare.db import artifact_api
from glare.tests.unit import base


class TestLocations(base.BaseTestArtifactAPI):
    """Test adding custom locations."""

    def setUp(self):
        super(TestLocations, self).setUp()
        values = {'name': 'ttt', 'version': '1.0'}
        self.sample_artifact = self.controller.create(
            self.req, 'sample_artifact', values)
        self.ct = 'application/vnd+openstack.glare-custom-location+json'

    def test_add_location(self):
        with mock.patch('glance_store.backend.add_to_backend') as mocked_add:
            body = {'url': 'https://FAKE_LOCATION.com',
                    'md5': "fake", 'sha1': "fake_sha", "sha256": "fake_sha256"}
            self.controller.upload_blob(
                self.req, 'sample_artifact', self.sample_artifact['id'],
                'blob', body, self.ct)
            art = self.controller.show(self.req, 'sample_artifact',
                                       self.sample_artifact['id'])
            self.assertEqual('active', art['blob']['status'])
            self.assertEqual('fake', art['blob']['md5'])
            self.assertEqual('fake_sha', art['blob']['sha1'])
            self.assertEqual('fake_sha256', art['blob']['sha256'])
            self.assertIsNone(art['blob']['size'])
            self.assertIsNone(art['blob']['content_type'])
            self.assertEqual('https://FAKE_LOCATION.com',
                             art['blob']['url'])
            self.assertNotIn('id', art['blob'])
            self.assertEqual(0, mocked_add.call_count)

        # Adding location for the second time leads to Conflict error
        body = {'url': 'https://ANOTHER_FAKE_LOCATION.com',
                'md5': "fake", 'sha1': "fake_sha", "sha256": "fake_sha256"}
        self.assertRaises(
            exc.Conflict, self.controller.upload_blob,
            self.req, 'sample_artifact', self.sample_artifact['id'],
            'blob', body, self.ct)

    def test_add_dict_location(self):
        with mock.patch('glance_store.backend.add_to_backend') as mocked_add:
            body = {'url': 'https://FAKE_LOCATION.com',
                    'md5': "fake", 'sha1': "fake_sha", "sha256": "fake_sha256"}
            self.controller.upload_blob(
                self.req, 'sample_artifact', self.sample_artifact['id'],
                'dict_of_blobs/blob', body, self.ct)
            art = self.controller.show(self.req, 'sample_artifact',
                                       self.sample_artifact['id'])
            self.assertEqual('active', art['dict_of_blobs']['blob']['status'])
            self.assertEqual('fake', art['dict_of_blobs']['blob']['md5'])
            self.assertEqual('fake_sha', art['dict_of_blobs']['blob']['sha1'])
            self.assertEqual('fake_sha256',
                             art['dict_of_blobs']['blob']['sha256'])
            self.assertIsNone(art['dict_of_blobs']['blob']['size'])
            self.assertIsNone(art['dict_of_blobs']['blob']['content_type'])
            self.assertEqual('https://FAKE_LOCATION.com',
                             art['dict_of_blobs']['blob']['url'])
            self.assertNotIn('id', art['blob'])
            self.assertEqual(0, mocked_add.call_count)

        # Adding location for the second time leads to Conflict error
        body = {'url': 'https://ANOTHER_FAKE_LOCATION.com',
                'md5': "fake", 'sha1': "fake_sha", "sha256": "fake_sha256"}
        self.assertRaises(
            exc.Conflict, self.controller.upload_blob,
            self.req, 'sample_artifact', self.sample_artifact['id'],
            'dict_of_blobs/blob', body, self.ct)

    def test_add_location_no_md5(self):
        body = {'url': 'https://FAKE_LOCATION.com',
                "sha1": "fake_sha", "sha256": "fake_sha256"}
        self.assertRaises(
            exc.BadRequest, self.controller.upload_blob,
            self.req, 'sample_artifact', self.sample_artifact['id'],
            'dict_of_blobs/blob', body, self.ct)

    def test_add_location_saving_blob(self):
        body = {'url': 'https://FAKE_LOCATION.com',
                'md5': "fake", 'sha1': "fake_sha", "sha256": "fake_sha256"}
        self.controller.upload_blob(
            self.req, 'sample_artifact', self.sample_artifact['id'],
            'blob', body, self.ct)
        art = self.controller.show(self.req, 'sample_artifact',
                                   self.sample_artifact['id'])

        # Change status of the blob to 'saving'
        art['blob']['status'] = 'saving'
        artifact_api.ArtifactAPI().update_blob(
            self.req.context, self.sample_artifact['id'],
            {'blob': art['blob']})
        art = self.controller.show(
            self.req, 'sample_artifact', self.sample_artifact['id'])
        self.assertEqual('saving', art['blob']['status'])

        body = {'url': 'https://ANOTHER_FAKE_LOCATION.com',
                'md5': "fake", 'sha1': "fake_sha", "sha256": "fake_sha256"}
        self.assertRaises(
            exc.Conflict, self.controller.upload_blob,
            self.req, 'sample_artifact', self.sample_artifact['id'],
            'blob', body, self.ct)

    def test_too_long_location_url(self):
        body = {'url': 'http://FAKE_LOCATION%s.com' % ('a' * 2049),
                'md5': "fake", 'sha1': "fake_sha", "sha256": "fake_sha256"}
        self.assertRaises(
            exc.BadRequest, self.controller.upload_blob,
            self.req, 'sample_artifact', self.sample_artifact['id'],
            'blob', body, self.ct)
