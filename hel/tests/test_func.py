import copy
import datetime
import os
import unittest

from pymongo import MongoClient
from webob.headers import ResponseHeaders

from hel.utils.messages import Messages
from hel.utils.tests import sample_packages as s_pkgs
from hel.utils.constants import Constants


deleted = False
auth_headers = None
mongodb_url = 'mongodb://localhost:37017'
if 'HEL_TESTING_MONGODB_ADDR' in os.environ:
    mongodb_url = os.environ['HEL_TESTING_MONGODB_ADDR']


class FunctionalTests(unittest.TestCase):

    user = {
        'nickname': 'root',
        'password': '/etc/passwd',
        'email': 'root@your.pc'
    }

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        global deleted
        if not deleted:
            mongo = MongoClient(mongodb_url)
            db = mongo.hel
            users = db['users']
            users.delete_many({})
            mongo.close()
            deleted = True

    def setUp(self):
        settings = {
            'activation.length': 64,
            'activation.time': 10,
            'mongo_db_url': mongodb_url
        }
        from hel import main
        app = main({}, **settings)
        from webtest import TestApp
        self.test_app = TestApp(app)

    def test_unexisting_page(self):
        self.test_app.get('/thispagedoesnotexist', status=404)

    def test_bad_log_in(self):
        res = self.test_app.post_json('/auth', {
                'password': 'hi',
                'action': 'log-in'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.bad_request)

    def test_failed_log_in(self):
        res = self.test_app.post_json('/auth', {
                'password': 'totally-random-passwd',
                'nickname': '-n0-such-user',
                'action': 'log-in'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.failed_login)

    def test_failed_log_in_empty_nick(self):
        res = self.test_app.post_json('/auth', {
                'password': 'hi',
                'nickname': '',
                'action': 'log-in'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.empty_nickname)

    def test_failed_log_in_empty_pass(self):
        res = self.test_app.post_json('/auth', {
                'password': '',
                'nickname': 'test',
                'action': 'log-in'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.empty_password)

    def test_bad_reg(self):
        res = self.test_app.post_json('/auth', {
                'email': '',
                'nickname': '',
                'action': 'register'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.bad_request)

    def test_failed_reg_empty_nick(self):
        res = self.test_app.post_json('/auth', {
                'email': '',
                'nickname': '',
                'password': '',
                'action': 'register'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.empty_nickname)

    def test_failed_reg_empty_email(self):
        res = self.test_app.post_json('/auth', {
                'email': '',
                'nickname': self.user['nickname'],
                'password': '',
                'action': 'register'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.empty_email)

    def test_failed_reg_empty_password(self):
        res = self.test_app.post_json('/auth', {
                'email': self.user['email'],
                'nickname': self.user['nickname'],
                'password': '',
                'action': 'register'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.empty_password)

    def test_failed_reg_nick_bad(self):
        res = self.test_app.post_json('/auth', {
                'action': 'register',
                'nickname': '!@#',
                'email': '123@mail.tld',
                'password': '123'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.user_bad_name)

    def test_reg_success(self):
        data = copy.copy(self.user)
        data['action'] = 'register'
        res = self.test_app.post_json('/auth', data, status=200)
        self.assertEqual(res.json['data'], Messages.account_created_success)
        client = MongoClient(mongodb_url)
        users = [x for x in client.hel['users'].find()]
        client.close()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['nickname'], data['nickname'])

    def test_no_action_auth(self):
        res = self.test_app.post_json('/auth', {
            'oh': 'well'
        }, status=400)
        self.assertEqual(res.json['message'], Messages.bad_request)

    def test_bad_json_auth(self):
        res = self.test_app.post('/auth', """hey there
            'oh': 'well'
        },""", status=400)
        self.assertEqual(res.json['message'], Messages.bad_request)

    def test_simple_cors_headers(self):
        res = self.test_app.post('/auth', status=400)
        self.assertTrue(any(
            v[0].lower() == 'access-control-allow-origin' and
            v[1] == '*' for v in res.headerlist))

    def test_preflight_cors_headers(self):
        headers = ResponseHeaders()
        headers.add('Origin', 'http://example.com')
        headers.add('Access-Control-Request-Method', 'POST')
        headers.add('Access-Control-Request-Headers', 'X-HELLO, Content-Type')
        res = self.test_app.options('/auth', status=200, headers=headers)
        self.assertTrue(any(
            v[0].lower() == 'access-control-allow-origin' and
            v[1] == 'http://example.com' for v in res.headerlist))
        self.assertTrue(any(
            v[0].lower() == 'access-control-allow-methods' and
            'POST' in v[1] for v in res.headerlist))
        self.assertTrue(any(
            v[0].lower() == 'access-control-allow-headers' and
            'X-HELLO, Content-Type' in v[1] for v in res.headerlist))


class FunctionalAuthTests(unittest.TestCase):

    user = FunctionalTests.user

    setUp = FunctionalTests.setUp
    tearDown = FunctionalTests.tearDown

    def test_failed_log_in_pass(self):
        data = copy.copy(self.user)
        data['action'] = 'log-in'
        data['password'] = 'blah-blah-blah'
        res = self.test_app.post_json('/auth', data, status=400)
        self.assertEqual(res.json['message'], Messages.failed_login)


class FunctionalTestsWithAuth(unittest.TestCase):

    user = FunctionalAuthTests.user

    def setUp(self):
        client = MongoClient(mongodb_url)
        client.hel['users'].delete_many({})
        client.close()
        FunctionalAuthTests.setUp(self)
        data = copy.copy(self.user)
        data['action'] = 'register'
        res = self.test_app.post_json('/auth', data, status=200)
        self.assertEqual(res.json['data'], Messages.account_created_success)
        client = MongoClient(mongodb_url)
        users = [x for x in client.hel['users'].find()]
        client.close()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['nickname'], data['nickname'])
        data = copy.copy(self.user)
        data['action'] = 'log-in'
        res = self.test_app.post_json('/auth', data, status=200)
        headers = res.headers
        auth_headers = ResponseHeaders()
        for k, v in headers.items():
            if k.lower() == 'set-cookie':
                auth_headers.add('Cookie', v)
        self.auth_headers = auth_headers
        res = self.test_app.get('/auth', headers=auth_headers, status=400)
        self.assertTrue(res.json['logged_in'])
        self.log_out_status = 200

    def tearDown(self):
        FunctionalAuthTests.tearDown(self)
        res = self.test_app.post_json('/auth', {
                'action': 'log-out'
            }, headers=self.auth_headers,
            status=self.log_out_status)
        self.auth_headers = None
        auth_headers = res.headers
        res = self.test_app.get('/auth', headers=auth_headers, status=400)
        self.assertFalse(res.json['logged_in'])
        client = MongoClient(mongodb_url)
        client.hel['users'].delete_many({})
        client.close()

    def test_log_in_log_out(self):
        pass

    def test_create_bad_pkg(self):
        self.test_app.post_json('/packages', {
                'name': 'hi',
                'blah': 'blah'
            }, headers=self.auth_headers, status=400)

    def test_upd_user(self):
        client = MongoClient(mongodb_url)
        client.hel['users'].update(
            {'nickname': 'root'},
            {'$set': {'groups': ['admins']}})
        client.close()
        self.test_app.patch_json('/users/root', {
                '$set': {
                    'groups': [
                        'hi'
                    ]
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/users/root',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertIn('hi', data['groups'])

    def test_get_non_existing_user(self):
        client = MongoClient(mongodb_url)
        client.hel['users'].update(
            {'nickname': 'root'},
            {'$set': {'groups': ['admins']}})
        client.close()
        self.test_app.get(
            '/users/non-existing-user',
            headers=self.auth_headers, status=404)

    def test_create_bad_user(self):
        client = MongoClient(mongodb_url)
        client.hel['users'].update(
            {'nickname': 'root'},
            {'$set': {'groups': ['admins']}})
        client.close()
        res = self.test_app.post_json('/users', {
                'nickname': 'hi'
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.bad_user, res.json['message'])

    def test_del_user(self):
        client = MongoClient(mongodb_url)
        client.hel['users'].update(
            {'nickname': 'root'},
            {'$set': {'groups': ['admins']}})
        client.close()
        self.test_app.delete(
            '/users/root',
            headers=self.auth_headers, status=204)
        self.log_out_status = 400

    def test_invalid_url(self):
        data = copy.deepcopy(s_pkgs.pkg1).data
        data['screenshots']['example.com/hey'] = "Oh, I'm missing the scheme!"
        data['name'] = 'package-missing-scheme'
        res = self.test_app.post_json('/packages', data,
                                      headers=self.auth_headers, status=400)
        self.assertEqual(res.json['message'], Messages.invalid_uri)

    def test_invalid_scheme(self):
        data = copy.deepcopy(s_pkgs.pkg2).data
        data['screenshots']['oh://my.dog'] = "Hello."
        data['name'] = 'package-bad-scheme'
        res = self.test_app.post_json('/packages', data,
                                      headers=self.auth_headers, status=400)
        self.assertEqual(res.json['message'], Messages.invalid_uri)

    def test_no_actions_performed_logged_in(self):
        res = self.test_app.post_json('/auth', {
                'action': 'log-in',
                'nickname': 'root',
                'password': 'oh-no'
            }, headers=self.auth_headers, status=200)
        self.assertEqual(res["data"], Messages.already_logged_in)

    def test_logged_in_profile(self):
        res = self.test_app.get('/profile',
                                headers=self.auth_headers, status=200)
        self.assertTrue(res.json['logged_in'])
        self.assertEqual(res.json['data']['nickname'], self.user['nickname'])


class FunctionalTestsWithReg(unittest.TestCase):

    user = FunctionalAuthTests.user

    def setUp(self):
        client = MongoClient(mongodb_url)
        client.hel['users'].delete_many({})
        client.close()
        FunctionalAuthTests.setUp(self)
        data = copy.copy(self.user)
        data['action'] = 'register'
        res = self.test_app.post_json('/auth', data, status=200)
        self.assertEqual(res.json['data'], Messages.account_created_success)
        client = MongoClient(mongodb_url)
        users = [x for x in client.hel['users'].find()]
        client.close()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['nickname'], data['nickname'])

    def test_failed_reg_nick_use(self):
        res = self.test_app.post_json('/auth', {
                'nickname': 'root',
                'email': 'asd',
                'password': '...',
                'action': 'register'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.nickname_in_use)

    def test_failed_reg_email_use(self):
        res = self.test_app.post_json('/auth', {
                'nickname': 'root2',
                'email': 'root@your.pc',
                'password': '...',
                'action': 'register'
            }, status=400)
        self.assertEqual(res.json['message'], Messages.email_in_use)

    def test_lst_users_no_params(self):
        res = self.test_app.get('/users', status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 1)

    def test_lst_users_group_0(self):
        res = self.test_app.get('/users', {
                'groups': 'hi'
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 0)

    def test_lst_users_offset_99(self):
        res = self.test_app.get('/users', {
                'offset': 99
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 0)

    def test_lst_users_bad_offset(self):
        res = self.test_app.get('/users', {
                'offset': 'hi'
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 1)

    def test_lst_users_group(self):
        client = MongoClient(mongodb_url)
        client.hel['users'].update(
            {'nickname': 'root'},
            {'$set': {'groups': ['admins']}})
        client.close()
        res = self.test_app.get('/users', {
                'groups': 'admins'
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 1)
        self.assertNotIn('password', data['list'][0])

    def test_logged_out_profile(self):
        res = self.test_app.get('/profile', status=200)
        self.assertFalse(res.json['logged_in'])
        self.assertEqual({}, res.json['data'])

    def tearDown(self):
        FunctionalAuthTests.tearDown(self)
        client = MongoClient(mongodb_url)
        client.hel['users'].delete_many({})
        client.close()


class FunctionalTestsWithPkg(unittest.TestCase):

    user = FunctionalTestsWithAuth.user

    pkg1 = s_pkgs.pkg1
    pkg2 = s_pkgs.pkg2
    pkg3 = s_pkgs.pkg3

    def setUp(self):
        FunctionalTestsWithAuth.setUp(self=self)
        client = MongoClient(mongodb_url)
        client.hel['packages'].delete_many({})
        client.close()
        for pkg in [self.pkg1, self.pkg2]:
            self.test_app.post('/packages', str(pkg),
                               headers=self.auth_headers, status=201)

    def tearDown(self):
        FunctionalTestsWithAuth.tearDown(self=self)
        client = MongoClient(mongodb_url)
        client.hel['packages'].delete_many({})
        client.close()

    def test_create_packages_success(self):
        pass

    def test_stats_views_increment(self):
        for i in range(3):
            self.test_app.get('/packages/package-2', status=200)
        res = self.test_app.get('/packages/package-2', status=200)
        self.assertEqual(res.json['data']['stats']['views'], 3)

    def test_upd_pkg_name_conflict(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'name': 'package-1'
            }, headers=self.auth_headers, status=409)
        self.assertEqual(Messages.pkg_name_conflict, res.json['message'])

    def test_upd_pkg_name_str(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'name': ['Hello', 'there']
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('name', 'str',),
                         res.json['message'])

    def test_upd_pkg_name_bad(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'name': 'hi.there'
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.pkg_bad_name,
                         res.json['message'])

    def test_upd_pkg_desc_str(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'description': ['Hello']
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('description', 'str',),
                         res.json['message'])

    def test_upd_pkg_owners_los(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'owners': 'Hi'
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('owners', 'list of strs',),
                         res.json['message'])

    def test_upd_pkg_owners_bad_name(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'owners': ['!@#$%^&*()']
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.user_bad_name, res.json['message'])

    def test_upd_pkg_owners_empty_list(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'owners': []
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.empty_owner_list, res.json['message'])

    def test_upd_pkg_owners_ok(self):
        self.test_app.patch_json('/packages/package-1', {
                'owners': ['hi']
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get('/packages/package-1', status=200)
        self.assertListEqual(res.json['data']['owners'], ['hi'])

    def test_upd_pkg_license_str(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'license': ['Hi']
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('license', 'str',),
                         res.json['message'])

    def test_upd_pkg_shdesc_str(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'short_description': ['Hi']
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % (
                         'short_description', 'str',), res.json['message'])

    def test_upd_pkg_authors_los(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'authors': 'test'
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('authors', 'list of strs',),
                         res.json['message'])

    def test_upd_pkg_tags_los(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'tags': 'test'
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('tags', 'list of strs',),
                         res.json['message'])

    def test_upd_pkg_ver_dict(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': 'test'
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('versions', 'dict',),
                         res.json['message'])

    def test_upd_pkg_ver_num_bad(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    'test': {}
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual("Version string lacks a numerical component: 'test'",
                         res.json['message'])

    def test_upd_pkg_ver_v_dict(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.0.0': 'hi :)'
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('version_info', 'dict',),
                         res.json['message'])

    def test_upd_pkg_ver_v_files_dict(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.2': {
                        'files': 'Hi :)'
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('files', 'dict',),
                         res.json['message'])

    def test_upd_pkg_ver_v_files_url_str(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.1.0': {
                        'files': {
                            'http://example.com/file15': 'test'
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('file_info', 'dict',),
                         res.json['message'])

    def test_upd_pkg_ver_v_files_dir_str(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.2': {
                        'files': {
                            'http://example.com/file28': {
                                'dir': 101
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('file_dir', 'str',),
                         res.json['message'])

    def test_upd_pkg_ver_v_files_name_str(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.1.1': {
                        'files': {
                            'http://example.com/file18': {
                                'name': 101
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('file_name', 'str',),
                         res.json['message'])

    def test_upd_pkg_ver_v_deps_dict(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.0': {
                        'depends': 'test'
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('depends', 'dict',),
                         res.json['message'])

    def test_upd_pkg_ver_v_deps_ver_str(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.1.0': {
                        'depends': {
                            'dpackage-1': {
                                'version': 222
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('dep_version', 'str',),
                         res.json['message'])

    def test_upd_pkg_ver_v_deps_ver_bad(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.1': {
                        'depends': {
                            'dpackage-4': {
                                'version': 'hi'
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual("Invalid requirement specification: 'hi'",
                         res.json['message'])

    def test_upd_pkg_ver_v_deps_ver_bad_2(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.1.0': {
                        'depends': {
                            'dpackage-1': {
                                'version': '666.*'
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual("Invalid version string: '666.*'",
                         res.json['message'])

    def test_upd_pkg_ver_v_deps_type_str(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.1': {
                        'depends': {
                            'dpackage-4': {
                                'type': 333
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('dep_type', 'str',),
                         res.json['message'])

    def test_upd_pkg_ver_v_deps_type_bad(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.1.0': {
                        'depends': {
                            'dpackage-1': {
                                'type': 'hello'
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.wrong_dep_type, res.json['message'])

    def test_upd_pkg_ver_none(self):
        self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.2': None
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/packages/package-2',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertNotIn('1.0.2', data['versions'])

    def test_upd_pkg_ver_v_files_url_none(self):
        self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.1.0': {
                        'files': {
                            'http://example.com/file15': None
                        }
                    }
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/packages/package-1',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertNotIn('http://example.com/file15',
                         data['versions']['1.1.0']['files'])

    def test_upd_pkg_ver_v_deps(self):
        self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.0': {
                        'depends': {
                            'dpackage-4': {
                                'version': '*'
                            },
                            'dpackage-42': {
                                'version': '^2.5',
                                'type': 'recommended'
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/packages/package-2',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertEqual(data['versions']['1.0.0']['depends']['dpackage-4']
                         ['version'], '*')
        self.assertIn('dpackage-42', data['versions']['1.0.0']['depends'])
        self.assertEqual(data['versions']['1.0.0']['depends']['dpackage-42']
                         ['version'], '^2.5')
        self.assertEqual(data['versions']['1.0.0']['depends']['dpackage-42']
                         ['type'], 'recommended')

    def test_upd_pkg_partial_new_ver(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.2.0': {
                        'files': {}
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.partial_ver, res.json['message'])

    def test_upd_pkg_partial_new_ver_files(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.0': {
                        'files': {
                            'http://example.com/file42': {
                                'dir': '/test'
                            }
                        },
                        'depends': {},
                        'changes': ''
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.partial_ver, res.json['message'])

    def test_upd_pkg_ver_v_files(self):
        self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.1.0': {
                        'files': {
                            'http://example.com/file42': {
                                'dir': '/bin',
                                'name': 'file42'
                            }
                        }
                    }
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/packages/package-1',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertIn('http://example.com/file42', data['versions']['1.1.0']
                      ['files'])
        self.assertEqual(data['versions']['1.1.0']['files']
                         ['http://example.com/file42']['dir'], '/bin')
        self.assertEqual(data['versions']['1.1.0']['files']
                         ['http://example.com/file42']['name'], 'file42')

    def test_upd_pkg_partial_dep(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.1.0': {
                        'files': {},
                        'depends': {
                            'dpackage-42': {
                                'version': '*'
                            }
                        },
                        'changes': ''
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.partial_ver, res.json['message'])

    def test_upd_pkg_ver_v_chgs_bad(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'versions': {
                    '1.0.0': {
                        'changes': ['o', 'h', 'a', 'i']
                    }
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('changes', 'str',),
                         res.json['message'])

    def test_upd_pkg_ver_v_chgs(self):
        self.test_app.patch_json('/packages/package-2', {
                'versions': {
                    '1.0.2': {
                        'changes': ':)'
                    }
                }
            }, headers=self.auth_headers, status=204)

    def test_upd_pkg_scr_dict(self):
        res = self.test_app.patch_json('/packages/package-1', {
                'screenshots': 'Hi'
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('screenshots', 'dict',),
                         res.json['message'])

    def test_upd_pkg_scr_desc_str(self):
        res = self.test_app.patch_json('/packages/package-2', {
                'screenshots': {
                    'http://img.example.com/img22': ['Test']
                }
            }, headers=self.auth_headers, status=400)
        self.assertEqual(Messages.type_mismatch % ('screenshot_desc', 'str',),
                         res.json['message'])

    def test_upd_pkg_scr_desc_none(self):
        self.test_app.patch_json('/packages/package-1', {
                'screenshots': {
                    'http://img.example.com/img12': None
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/packages/package-1',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertNotIn('http://img.example.com/img12', data['screenshots'])

    def test_upd_pkg_scr(self):
        self.test_app.patch_json('/packages/package-2', {
                'screenshots': {
                    'http://img.example.com/img20': 'Hi! :)'
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/packages/package-2',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertIn('http://img.example.com/img20', data['screenshots'])
        self.assertEqual(data['screenshots']['http://img.example.com/img20'],
                         'Hi! :)')

    def test_upd_pkg_scr_empty_str(self):
        self.test_app.patch_json('/packages/package-1', {
                'screenshots': {
                    'http://img.example.com/img10': ''
                }
            }, headers=self.auth_headers, status=204)
        res = self.test_app.get(
            '/packages/package-1',
            headers=self.auth_headers, status=200)
        data = res.json['data']
        self.assertIn('http://img.example.com/img10', data['screenshots'])
        self.assertEqual(data['screenshots']['http://img.example.com/img10'],
                         '')

    def test_get_non_existing_pkg(self):
        self.test_app.get('/packages/hi-there', status=404)

    def test_del_pkg(self):
        self.test_app.delete(
            '/packages/package-2',
            headers=self.auth_headers, status=204)

    def test_crt_pkg_owners_bad_user(self):
        pkg = copy.deepcopy(self.pkg3.data)
        pkg['name'] = 'package-1'
        pkg['owners'] = ['!@#$%^&*()_+|']
        res = self.test_app.post_json('/packages', pkg,
                                      headers=self.auth_headers, status=400)
        self.assertEqual(Messages.user_bad_name, res.json['message'])

    def test_crt_pkg_owners_empty(self):
        pkg = copy.deepcopy(self.pkg3.data)
        pkg['name'] = 'package-2'
        pkg['owners'] = []
        res = self.test_app.post_json('/packages', pkg,
                                      headers=self.auth_headers, status=400)
        self.assertEqual(Messages.empty_owner_list, res.json['message'])

    def test_crt_pkg_name_conflict(self):
        pkg = copy.copy(self.pkg3.data)
        pkg['name'] = 'package-1'
        res = self.test_app.post_json(
            '/packages', pkg,
            headers=self.auth_headers, status=409)
        self.assertEqual(Messages.pkg_name_conflict, res.json['message'])

    def test_crt_pkg_name_bad(self):
        pkg = copy.copy(self.pkg3.data)
        pkg['name'] = 'hi.there'
        res = self.test_app.post_json(
            '/packages', pkg,
            headers=self.auth_headers, status=400)
        self.assertEqual(Messages.pkg_bad_name, res.json['message'])

    def test_lst_pkgs_no_params(self):
        res = self.test_app.get('/packages', {
                'name': 'age pack'
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 2)

    def test_lst_pkgs_bad_offset(self):
        res = self.test_app.get('/packages', {
                'name': 'age pack',
                'offset': 'hi'
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 2)

    def test_lst_pkgs_offset_1(self):
        res = self.test_app.get('/packages', {
                'name': 'a ge p ck',
                'offset': 1
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 1)

    def test_lst_pkgs_offset_99(self):
        res = self.test_app.get('/packages', {
                'name': 'a ge - "pack" 2',
                'offset': 99
            }, status=200)
        data = res.json['data']
        self.assertEqual(len(data['list']), 0)

    def test_get_pkg_date_field(self):
        res = self.test_app.get('/packages/package-1', status=200)
        self.assertIn('date', res.json['data']['stats'])
        self.assertIn('created', res.json['data']['stats']['date'])
        self.assertIn('last-updated', res.json['data']['stats']['date'])
        self.assertEqual(res.json['data']['stats']['date']['created'],
                         res.json['data']['stats']['date']['last-updated'])
        self.assertIsNotNone(datetime.datetime.strptime(
            res.json['data']['stats']['date']['created'],
            Constants.date_format))
