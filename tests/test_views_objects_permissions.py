import unittest

from kinto.core.testing import get_user_headers

from .support import (BaseWebTest,
                      MINIMALIST_BUCKET, MINIMALIST_COLLECTION,
                      MINIMALIST_GROUP, MINIMALIST_RECORD)


class PermissionsTest(BaseWebTest, unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(PermissionsTest, self).__init__(*args, **kwargs)
        self.alice_headers = self.headers.copy()
        self.alice_headers.update(**get_user_headers('alice'))
        self.bob_headers = self.headers.copy()
        self.bob_headers.update(**get_user_headers('bob'))

        self.alice_principal = ('basicauth:d5b0026601f1b251974e09548d44155e16'
                                '812e3c64ff7ae053fe3542e2ca1570')
        self.bob_principal = ('basicauth:c031ced27503f788b102ca54269a062ec737'
                              '94bb075154c74a0d4311e74ca8b6')


class BucketPermissionsTest(PermissionsTest):

    def setUp(self):
        bucket = MINIMALIST_BUCKET.copy()
        bucket['permissions'] = {'read': [self.alice_principal]}
        self.app.put_json('/buckets/sodas',
                          bucket,
                          headers=self.headers)

    def test_creation_is_allowed_to_authenticated_by_default(self):
        self.app.put_json('/buckets/beer',
                          MINIMALIST_BUCKET,
                          headers=self.headers)

    def test_current_user_receives_write_permission_on_creation(self):
        resp = self.app.put_json('/buckets/beer',
                                 MINIMALIST_BUCKET,
                                 headers=self.headers)
        permissions = resp.json['permissions']
        self.assertIn(self.principal, permissions['write'])

    def test_can_read_if_allowed(self):
        self.app.get('/buckets/sodas',
                     headers=self.alice_headers)

    def test_cannot_write_if_not_allowed(self):
        self.app.put_json('/buckets/sodas',
                          MINIMALIST_BUCKET,
                          headers=self.alice_headers,
                          status=403)

    def test_permissions_are_not_returned_if_can_only_read(self):
        resp = self.app.get('/buckets/sodas', headers=self.alice_headers)
        self.assertNotIn('permissions', resp.json)

    def test_permissions_are_returned_if_can_write(self):
        resp = self.app.get('/buckets/sodas', headers=self.headers)
        self.assertIn('permissions', resp.json)


class CollectionPermissionsTest(PermissionsTest):

    def setUp(self):
        bucket = MINIMALIST_BUCKET.copy()
        bucket['permissions'] = {
            'read': [self.alice_principal],
            'write': [self.bob_principal]
        }
        self.app.put_json('/buckets/beer',
                          bucket,
                          headers=self.headers)
        self.app.put_json('/buckets/beer/collections/barley',
                          MINIMALIST_COLLECTION,
                          headers=self.headers)

    def test_read_is_allowed_if_read_on_bucket(self):
        self.app.get('/buckets/beer/collections/barley',
                     headers=self.alice_headers)

    def test_read_is_allowed_if_write_on_bucket(self):
        self.app.get('/buckets/beer/collections/barley',
                     headers=self.bob_headers)

    def test_cannot_read_if_not_allowed(self):
        headers = self.headers.copy()
        headers.update(**get_user_headers('jean-louis'))
        self.app.get('/buckets/beer/collections/barley',
                     headers=headers,
                     status=403)

    def test_cannot_write_if_not_allowed(self):
        self.app.put_json('/buckets/beer/collections/barley',
                          MINIMALIST_COLLECTION,
                          headers=self.alice_headers,
                          status=403)


class GroupPermissionsTest(PermissionsTest):

    def setUp(self):
        bucket = MINIMALIST_BUCKET.copy()
        bucket['permissions'] = {
            'read': [self.alice_principal],
            'write': [self.bob_principal]
        }
        self.app.put_json('/buckets/beer',
                          bucket,
                          headers=self.headers)

        self.app.put_json('/buckets/beer/groups/moderators',
                          MINIMALIST_GROUP,
                          headers=self.headers)

    def test_creation_is_allowed_if_write_on_bucket(self):
        self.app.post_json('/buckets/beer/groups',
                           MINIMALIST_GROUP,
                           headers=self.headers)

    def test_read_is_allowed_if_read_on_bucket(self):
        self.app.get('/buckets/beer/groups/moderators',
                     headers=self.alice_headers)

    def test_read_is_allowed_if_write_on_bucket(self):
        self.app.get('/buckets/beer/groups/moderators',
                     headers=self.bob_headers)

    def test_cannot_read_if_not_allowed(self):
        headers = self.headers.copy()
        headers.update(**get_user_headers('jean-louis'))
        self.app.get('/buckets/beer/groups/moderators',
                     headers=headers,
                     status=403)

    def test_cannot_write_if_not_allowed(self):
        self.app.put_json('/buckets/beer/groups/moderators',
                          MINIMALIST_GROUP,
                          headers=self.alice_headers,
                          status=403)

    def test_creation_is_forbidden_is_no_write_on_bucket(self):
        self.app.post_json('/buckets/beer/groups',
                           MINIMALIST_GROUP,
                           headers=self.alice_headers,
                           status=403)


class RecordPermissionsTest(PermissionsTest):

    def setUp(self):
        bucket = MINIMALIST_BUCKET.copy()
        bucket['permissions'] = {'write': [self.alice_principal]}
        self.app.put_json('/buckets/beer',
                          bucket,
                          headers=self.headers)

        collection = MINIMALIST_COLLECTION.copy()
        collection['permissions'] = {'write': [self.bob_principal]}
        self.app.put_json('/buckets/beer/collections/barley',
                          collection,
                          headers=self.headers)

    def test_creation_is_allowed_if_write_on_bucket(self):
        self.app.post_json('/buckets/beer/collections/barley/records',
                           MINIMALIST_RECORD,
                           headers=self.alice_headers)

    def test_creation_is_allowed_if_write_on_collection(self):
        self.app.post_json('/buckets/beer/collections/barley/records',
                           MINIMALIST_RECORD,
                           headers=self.bob_headers)

    def test_creation_is_forbidden_is_no_write_on_bucket_nor_collection(self):
        headers = self.headers.copy()
        headers.update(**get_user_headers('jean-louis'))
        self.app.post_json('/buckets/beer/collections/barley/records',
                           MINIMALIST_RECORD,
                           headers=headers,
                           status=403)

    def test_record_permissions_are_modified_by_patch(self):
        collection_url = '/buckets/beer/collections/barley/records'
        resp = self.app.post_json(collection_url,
                                  MINIMALIST_RECORD,
                                  headers=self.headers)
        record = resp.json['data']
        resp = self.app.patch_json(collection_url + '/' + record['id'],
                                   {'permissions': {'read': ['fxa:user']}},
                                   headers=self.headers)
        self.assertIn('fxa:user', resp.json['permissions']['read'])


class ChildrenCreationTest(PermissionsTest):
    def setUp(self):
        self.app.put_json('/buckets/create',
                          {'permissions': {'group:create': ['system.Authenticated']}},
                          headers=self.alice_headers)
        self.app.put_json('/buckets/write',
                          {'permissions': {'write': ['system.Authenticated']}},
                          headers=self.alice_headers)
        self.app.put_json('/buckets/read',
                          {'permissions': {'read': ['system.Authenticated']}},
                          headers=self.alice_headers)
        for parent in ('create', 'write', 'read'):
            self.app.put_json('/buckets/%s/groups/child' % parent,
                              MINIMALIST_GROUP,
                              headers=self.alice_headers)
        self.bob_headers_safe_creation = dict({'If-None-Match': '*'},
                                              **self.bob_headers)

    def test_cannot_read_others_objects_if_only_allowed_to_create(self):
        self.app.get('/buckets/create/groups', headers=self.bob_headers, status=403)
        self.app.get('/buckets/create/groups/child', headers=self.bob_headers, status=403)

    def test_safe_creation_with_put_returns_412_if_allowed_to_create(self):
        self.app.put_json('/buckets/create/groups/child',
                          MINIMALIST_GROUP,
                          headers=self.bob_headers_safe_creation, status=412)

    def test_safe_creation_with_post_returns_412_if_allowed_to_create(self):
        self.app.post_json('/buckets/create/groups',
                           {'data': {'id': 'child', 'members': []}},
                           headers=self.bob_headers_safe_creation, status=412)

    def test_safe_creation_with_put_returns_412_if_allowed_to_write(self):
        self.app.put_json('/buckets/write/groups/child',
                          MINIMALIST_GROUP,
                          headers=self.bob_headers_safe_creation, status=412)

    def test_safe_creation_with_post_returns_412_if_allowed_to_write(self):
        self.app.post_json('/buckets/write/groups',
                           {'data': {'id': 'child', 'members': []}},
                           headers=self.bob_headers_safe_creation, status=412)

    def test_safe_creation_with_put_returns_403_if_only_allowed_to_read(self):
        self.app.put_json('/buckets/read/groups/child',
                          MINIMALIST_GROUP,
                          headers=self.bob_headers_safe_creation, status=403)

    def test_safe_creation_with_post_returns_403_if_only_allowed_to_read(self):
        self.app.post_json('/buckets/read/groups',
                           {'data': {'id': 'child', 'members': []}},
                           headers=self.bob_headers_safe_creation, status=403)
