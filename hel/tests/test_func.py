import copy
import unittest

from hel.utils.messages import Messages


class FunctionalTests(unittest.TestCase):

    user = {
        'nickname': 'root',
        'password': '/etc/passwd',
        'email': 'root@your.pc'
    }

    def __init__(self, *args, **kwargs):
        unittest.defaultTestLoader.sortTestMethodsUsing = None
        unittest.TestCase.__init__(self, *args, **kwargs)
        from pymongo import MongoClient
        url = 'mongodb://localhost:37017'
        mongo = MongoClient(url)
        db = mongo.hel
        users = db['users']
        users.delete_many({})
        mongo.close()

    def setUp(self):
        settings = {
            'activation.length': 64,
            'activation.time': 10,
            'mongo_db_url': 'mongodb://localhost:37017'
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

    def test_failed_log_in(self):
        res = self.test_app.post('/', {
                'password': 'totally-random-passwd',
                'nickname': '-n0-such-user',
                'log-in': True
            }, status=200)
        self.assertIsNone(res.html.find(id='log-out'))

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

    def test_failed_reg_passwd_match(self):
        res = self.test_app.post('/', {
                'email': self.user['email'],
                'nickname': self.user['nickname'],
                'password': self.user['password'],
                'passwd-confirm': 'Hello.',
                'register': True
            }, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.password_mismatch)

    def test_reg_success(self):
        data = copy.copy(self.user)
        data['register'] = True
        data['passwd-confirm'] = data['password']
        res = self.test_app.post('/', data, status=200)
        message = res.html.find(id='login-message')
        self.assertIsNotNone(message)
        self.assertEqual(message.string, Messages.account_created_success)


class FunctionalTestsWithAuth:

    user = FunctionalTests.user

    __init__ = FunctionalTests.__init__
    setUp = FunctionalTests.setUp
    tearDown = FunctionalTests.tearDown

    def test_log_in_success(self):
        data = copy.copy(self.user)
        data['log-in'] = True
        res1 = self.test_app.post('/', data, status=302)
        self.headers = res1.headers
        res = self.test_app.get('/', headers=self.headers, status=200)
        self.assertIsNone(res.html.find(id='login-message'))
        self.assertIsNone(res.html.find(id='action-log-in'))
        self.assertIsNone(res.html.find(id='action-register'))
        self.assertIsNone(res.html.find(id='log-in-form'))
        self.assertIsNone(res.html.find(id='register-form'))
        logout = res.html.find(id='log-out')
        self.assertIsNotNone(logout)
        self.assertEqual(logout.form.span.span.string, '@' +
                         self.user['nickname'])

    def test_log_out(self):
        res1 = self.test_app.post('/', {
                'log-out': True
            }, headers=self.headers, status=302)
        self.headers = res1.headers
        res = self.test_app.get('/', headers=self.headers, status=200)
        self.assertIsNotNone(res.html.find(id='login-message'))
