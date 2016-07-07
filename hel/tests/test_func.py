import copy
import os
import unittest
from webob.headers import ResponseHeaders

from hel.utils.messages import Messages
from hel.utils.tests import sample_packages as s_pkgs


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
            from pymongo import MongoClient
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

    def test_home(self):
        res = self.test_app.get('/', status=200)
        self.assertTrue(len(res.forms) > 0)

    def test_unexisting_page(self):
        self.test_app.get('/thispagedoesnotexist', status=404)

    def test_bad_log_in(self):
        res = self.test_app.post('/', {
                'password': 'hi',
                'log-in': True
            }, status=200)
        self.assertIsNone(res.html.find(id='log-out'))
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.bad_request)

    def test_failed_log_in(self):
        res = self.test_app.post('/', {
                'password': 'totally-random-passwd',
                'nickname': '-n0-such-user',
                'log-in': True
            }, status=200)
        self.assertIsNone(res.html.find(id='log-out'))

    def test_failed_log_in_empty_nick(self):
        res = self.test_app.post('/', {
                'password': 'hi',
                'nickname': '',
                'log-in': True
            }, status=200)
        self.assertIsNone(res.html.find(id='log-out'))
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.empty_nickname)

    def test_failed_log_in_empty_pass(self):
        res = self.test_app.post('/', {
                'password': '',
                'nickname': 'test',
                'log-in': True
            }, status=200)
        self.assertIsNone(res.html.find(id='log-out'))
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.empty_password)

    def test_bad_reg(self):
        res = self.test_app.post('/', {
                'email': '',
                'nickname': '',
                'passwd-confirm': '',
                'register': True
            }, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.bad_request)

    def test_failed_reg_empty_nick(self):
        res = self.test_app.post('/', {
                'email': '',
                'nickname': '',
                'password': '',
                'passwd-confirm': '',
                'register': True
            }, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.empty_nickname)

    def test_failed_reg_empty_email(self):
        res = self.test_app.post('/', {
                'email': '',
                'nickname': self.user['nickname'],
                'password': '',
                'passwd-confirm': '',
                'register': True
            }, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.empty_email)

    def test_failed_reg_empty_password(self):
        res = self.test_app.post('/', {
                'email': self.user['email'],
                'nickname': self.user['nickname'],
                'password': '',
                'passwd-confirm': '',
                'register': True
            }, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.empty_password)

    def test_failed_reg_nick_use(self):
        data = copy.copy(self.user)
        data['register'] = True
        data['passwd-confirm'] = 'hi'
        res = self.test_app.post('/', data, status=200)
        self.assertIsNone(res.html.find(id='log-out'))
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.password_mismatch)

    def test_reg_success(self):
        from pymongo import MongoClient
        data = copy.copy(self.user)
        data['register'] = True
        data['passwd-confirm'] = data['password']
        res = self.test_app.post('/', data, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.account_created_success)
        client = MongoClient(mongodb_url)
        users = [x for x in client.hel['users'].find()]
        client.close()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['nickname'], data['nickname'])

    def test_teapot(self):
        self.test_app.post('/teapot', status=418)


class FunctionalAuthTests(unittest.TestCase):

    user = FunctionalTests.user

    setUp = FunctionalTests.setUp
    tearDown = FunctionalTests.tearDown

    def test_failed_log_in_pass(self):
        data = copy.copy(self.user)
        data['log-in'] = True
        data['password'] = 'blah-blah-blah'
        res = self.test_app.post('/', data, status=200)
        self.assertIsNone(res.html.find(id='log-out'))
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.failed_login)


class FunctionalTestsWithAuth(unittest.TestCase):

    user = FunctionalAuthTests.user

    def setUp(self):
        from pymongo import MongoClient
        client = MongoClient(mongodb_url)
        client.hel['users'].delete_many({})
        client.close()
        FunctionalAuthTests.setUp(self)
        data = copy.copy(self.user)
        data['register'] = True
        data['passwd-confirm'] = data['password']
        res = self.test_app.post('/', data, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.account_created_success)
        client = MongoClient(mongodb_url)
        users = [x for x in client.hel['users'].find()]
        client.close()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['nickname'], data['nickname'])
        data = copy.copy(self.user)
        data['log-in'] = True
        res = self.test_app.post('/', data, status=302)
        headers = res.headers
        auth_headers = ResponseHeaders()
        for k, v in headers.items():
            if k.lower() == 'set-cookie':
                auth_headers.add('Cookie', v)
            elif k.lower() not in ['content-type', 'content-length']:
                auth_headers.add(k, v)
        self.auth_headers = auth_headers
        res = self.test_app.get('/', headers=auth_headers, status=200)
        self.assertIsNone(res.html.find(id='login-message'))
        self.assertIsNone(res.html.find(id='action-log-in'))
        self.assertIsNone(res.html.find(id='action-register'))
        self.assertIsNone(res.html.find(id='log-in-form'))
        self.assertIsNone(res.html.find(id='register-form'))
        logout = res.html.find(id='log-out')
        self.assertIsNotNone(logout)
        self.assertEqual(logout.form.span.span.string, '@' +
                         self.user['nickname'])

    def tearDown(self):
        FunctionalAuthTests.tearDown(self)
        res = self.test_app.post('/', {
                'log-out': True,
            }, headers=self.auth_headers, status=302)
        self.auth_headers = None
        auth_headers = res.headers
        res = self.test_app.get('/', headers=auth_headers, status=200)
        self.assertIsNotNone(res.html.find(id='login-message'))
        from pymongo import MongoClient
        client = MongoClient(mongodb_url)
        client.hel['users'].delete_many({})
        client.close()

    def test_log_in_log_out(self):
        pass

    def test_create_bad_pkg(self):
        res = self.test_app.post('/packages', """{
                "name": "hi",
                "blah": "blah"
            }""", headers=self.auth_headers, status=400)
        self.assertIn(Messages.bad_package, str(res.text))


class FunctionalTestsWithReg(unittest.TestCase):

    user = FunctionalAuthTests.user

    def setUp(self):
        from pymongo import MongoClient
        client = MongoClient(mongodb_url)
        client.hel['users'].delete_many({})
        client.close()
        FunctionalAuthTests.setUp(self)
        data = copy.copy(self.user)
        data['register'] = True
        data['passwd-confirm'] = data['password']
        res = self.test_app.post('/', data, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.account_created_success)
        client = MongoClient(mongodb_url)
        users = [x for x in client.hel['users'].find()]
        client.close()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['nickname'], data['nickname'])

    def test_failed_reg_nick_use(self):
        res = self.test_app.post('/', {
                'nickname': 'root',
                'email': 'asd',
                'password': '...',
                'passwd-confirm': '...',
                'register': True
            }, status=200)
        self.assertIsNone(res.html.find(id='log-out'))
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.nickname_in_use)

    def test_failed_reg_email_use(self):
        res = self.test_app.post('/', {
                'nickname': 'root2',
                'email': 'root@your.pc',
                'password': '...',
                'passwd-confirm': '...',
                'register': True
            }, status=200)
        self.assertIsNone(res.html.find(id='log-out'))
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.email_in_use)

    def tearDown(self):
        FunctionalAuthTests.tearDown(self)
        from pymongo import MongoClient
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
        from pymongo import MongoClient
        client = MongoClient(mongodb_url)
        client.hel['packages'].delete_many({})
        client.close()
        for pkg in [self.pkg1, self.pkg2, self.pkg3]:
            self.test_app.post('/packages', pkg.pkg,
                               headers=self.auth_headers, status=201)

    def tearDown(self):
        FunctionalTestsWithAuth.tearDown(self=self)
        from pymongo import MongoClient
        client = MongoClient(mongodb_url)
        client.hel['packages'].delete_many({})
        client.close()

    def create_packages_success(self):
        pass
