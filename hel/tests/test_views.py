import json
import os
import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest

from hel.utils.messages import Messages
from hel.utils.tests import sample_packages as s_pkgs, are_equal


from hel.utils.query import PackagesSearcher


class ViewTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_view_home(self):
        from hel.views import home
        request = testing.DummyRequest()
        info = home(request)
        self.assertEqual(info['project'], 'hel')


def one_value_param(name):

    def wrap(func):

        def f(self):
            tests = func(self)

            # 0 values: should fail
            with self.subTest(test='0 values'):
                try:
                    PackagesSearcher({
                        name: []
                    })()
                except HTTPBadRequest as e:
                    if (json.loads(e.body.decode('utf-8'))
                            ['message'] == Messages.no_values % name):
                        # Expected exception
                        pass
                    else:
                        raise e
                else:
                    raise AssertionError()

            # 2, 3 values: should fail
            for i in range(2, 4):
                with self.subTest(test='%s values' % i):
                    try:
                        PackagesSearcher({
                            name: ['hel'] * i
                        })()
                    except HTTPBadRequest as e:
                        if (json.loads(e.body.decode('utf-8'))
                                ['message'] == Messages.too_many_values % (
                                1, i)):
                            # Expected exception
                            pass
                        else:
                            raise e
                    else:
                        raise AssertionError()

            for test_case in tests:
                with self.subTest(test=test_case):
                    value, expected = test_case
                    searcher = PackagesSearcher({
                        name: [value]
                    })
                    searcher()
                    packages = [x for x in self.db['packages'].find({})]
                    search_result = searcher.search(packages)
                    for num, doc in enumerate(search_result):
                        if '_id' in search_result[num]:
                            del search_result[num]['_id']
                    self.assertTrue(are_equal(search_result, expected))

        return f

    return wrap


def param(name):

    def wrap(func):

        def f(self):

            tests = func(self)

            # Zero values: should fail
            with self.subTest(test='0 values'):
                try:
                    PackagesSearcher({
                        name: []
                    })()
                except HTTPBadRequest as e:
                    if (json.loads(e.body.decode('utf-8'))
                            ['message'] == Messages.no_values % name):
                        # Expected exception
                        pass
                    else:
                        raise e
                else:
                    raise AssertionError()

            for test_case in tests:
                with self.subTest(test=test_case):
                    values, expected = test_case
                    searcher = PackagesSearcher({
                        name: values
                    })
                    searcher()
                    packages = [x for x in self.db['packages'].find({})]
                    search_result = searcher.search(packages)
                    for num, doc in enumerate(search_result):
                        if '_id' in search_result[num]:
                            del search_result[num]['_id']
                    self.assertTrue(are_equal(search_result, expected))

        return f

    return wrap


class PkgSearchTests(unittest.TestCase):

    pkg1m = s_pkgs.pkg1
    pkg2m = s_pkgs.pkg2
    pkg3m = s_pkgs.pkg3

    def setUp(self):
        from pymongo import MongoClient

        url = 'mongodb://localhost:37017'
        if 'HEL_TESTING_MONGODB_ADDR' in os.environ:
            url = os.environ['HEL_TESTING_MONGODB_ADDR']
        self.client = MongoClient(url)
        self.db = self.client.hel
        self.db['packages'].delete_many({})
        self.pkg1 = self.pkg1m.data
        self.pkg2 = self.pkg2m.data
        self.pkg3 = self.pkg3m.data
        self.db['packages'].insert_one(self.pkg1m.pkg)
        self.db['packages'].insert_one(self.pkg2m.pkg)
        self.db['packages'].insert_one(self.pkg3m.pkg)

        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        self.db['packages'].delete_many({})
        self.client.close()

    @one_value_param('name')
    def test_pkg_search_name(self):
        return [
            ('package', [self.pkg1, self.pkg2, self.pkg3],),
            ('1', [self.pkg1],),
            ('p "ack" g e 2', [self.pkg2])
        ]

    @one_value_param('description')
    def test_pkg_search_description(self):
        return [
            ('y', [self.pkg1, self.pkg2, self.pkg3],),
            ('first', [self.pkg1],),
            ('second', [self.pkg2],),
            ('third', [self.pkg3],),
            ('test', [self.pkg1, self.pkg2, self.pkg3],),
            ('t "es" t', [self.pkg1, self.pkg2, self.pkg3],)
        ]

    @one_value_param('short_description')
    def test_pkg_search_short_description(self):
        return [
            ('pack', [self.pkg1, self.pkg2, self.pkg3],),
            ('3', [self.pkg3],),
            ('4', [],)
        ]

    @one_value_param('authors')
    def test_pkg_search_author(self):
        return [
            ('Tester', [self.pkg1, self.pkg2, self.pkg3],),
            ('Kjers', [self.pkg2],)
        ]

    @one_value_param('screen_desc')
    def test_pkg_search_screen_desc(self):
        return [
            ('3', [self.pkg1, self.pkg2, self.pkg3],),
            ('test-3', [self.pkg3],),
            ('te s "t-1"', [self.pkg1],)
        ]

    @param('license')
    def test_pkg_search_license(self):
        return [
            (['mylicense-1'], [self.pkg1],),
            (['mylicense-4'], [],),
            (['mylicense-3'], [self.pkg3],)
        ]

    @param('tags')
    def test_pkg_search_tags(self):
        return [
            (['xxx', 'zzz'], [self.pkg1],),
            (['aaa'], [self.pkg1, self.pkg3],),
            (['ccc'], [self.pkg2, self.pkg3],)
        ]

    @param('file_url')
    def test_pkg_search_file_url(self):
        return [
            (['http://example.com/file11'], [],),
            (['http://example.com/file19'], [self.pkg1],),
            (['http://example.com/file39'], [self.pkg3],),
            (['http://example.com/file28',
              'http://example.com/file29'], [self.pkg2],),
            (['http://example.com/file12',
              'http://example.com/file32'], [],),
            (['http://example.com/file29'], [self.pkg2],)
        ]

    @param('file_dir')
    def test_pkg_search_file_dir(self):
        return [
            (['/bin'], [self.pkg1, self.pkg2, self.pkg3],),
            (['/lib', '/man'], [self.pkg1, self.pkg2, self.pkg3],),
            (['/hey'], [],)
        ]

    @param('file_name')
    def test_pkg_search_file_name(self):
        return [
            (['test-3-file-1', 'test-1-file-3'], [],),
            (['test-2-file-2', 'test-2-file-3'], [],),
            (['test-1-file-1', 'test-1-file-2'], [],),
            (['test-3-file-7', 'test-2-file-9'], [],),
            (['test-2-file-8', 'test-2-file-7'], [self.pkg2],),
            (['test-1-file-7', 'test-1-file-8'], [self.pkg1],),
            (['test-3-file-2', 'test-3-file-9'], [],)
        ]

    @param('dependency')
    def test_pkg_search_dependency(self):
        return [
            (['dpackage-8:^3.5'], [self.pkg3],),
            (['dpackage-8:^3.5:required'], []),
            (['dpackage-1:6.6.6:recommended'], [],),
            (['dpackage-2'], [self.pkg1],)
        ]

    @param('screen_url')
    def test_pkg_search_screen_url(self):
        return [
            (['http://img.example.com/img11',
              'http://img.example.com/img31'], [],),
            (['http://img.example.com/img21',
              'http://img.example.com/img23'], [self.pkg2],),
            (['http://img.example.com/img42'], [],),
            (['http://img.example.com/img32'], [self.pkg3],)
        ]

    def test_bad_search_param(self):
        try:
            PackagesSearcher({'hi': ['test']})()
        except HTTPBadRequest as e:
            self.assertEqual(json.loads(e.body.decode('utf-8'))['message'],
                             Messages.bad_search_param % 'hi')
        else:
            raise AssertionError()
