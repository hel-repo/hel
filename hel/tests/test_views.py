import os
import unittest

from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest

from hel.utils.messages import Messages
from hel.utils.models import ModelPackage
from hel.utils.query import PackagesSearchQuery


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


# http://stackoverflow.com/a/8866661
def are_equal(a, b):
    unmatched = list(b)
    for element in a:
        try:
            unmatched.remove(element)
        except ValueError:
            return False
    return not unmatched


def one_value_param(name):

    def wrap(func):

        def f(self):
            tests = func(self)

            # 0 values: should fail
            with self.subTest(test='0 values'):
                try:
                    PackagesSearchQuery({
                        name: []
                    })()
                except HTTPBadRequest as e:
                    if str(e) == Messages.no_values % name:
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
                        PackagesSearchQuery({
                            name: ['hel'] * i
                        })()
                    except HTTPBadRequest as e:
                        if str(e) == Messages.too_many_values % (1, i):
                            # Expected exception
                            pass
                        else:
                            raise e
                    else:
                        raise AssertionError()

            for test_case in tests:
                with self.subTest(test=test_case):
                    value, expected = test_case
                    search_query = PackagesSearchQuery({
                        name: [value]
                    })
                    query = search_query()
                    search_result = [x for x in self.db
                                     ['packages'].find(query)]
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
                    PackagesSearchQuery({
                        name: []
                    })()
                except HTTPBadRequest as e:
                    if str(e) == Messages.no_values % name:
                        # Expected exception
                        pass
                    else:
                        raise e
                else:
                    raise AssertionError()

            for test_case in tests:
                with self.subTest(test=test_case):
                    values, expected = test_case
                    search_query = PackagesSearchQuery({
                        name: values
                    })
                    query = search_query()
                    search_result = [x for x in self.db
                                     ['packages'].find(query)]
                    for num, doc in enumerate(search_result):
                        if '_id' in search_result[num]:
                            del search_result[num]['_id']
                    self.assertTrue(are_equal(search_result, expected))

        return f

    return wrap


class PkgSearchTests(unittest.TestCase):

    pkg1 = ModelPackage(
        name='package-1',
        description='My first test package.',
        short_description='1 package.',
        owner='Tester',
        authors=['Tester', 'Crackes'],
        license='mylicense-1',
        tags=['aaa', 'xxx', 'zzz'],
        versions={
            '1.1.1': {
                'files': {
                    'http://example.com/file17': {
                        'dir': '/bin',
                        'name': 'test-1-file-7'
                    },
                    'http://example.com/file18': {
                        'dir': '/lib',
                        'name': 'test-1-file-8'
                    },
                    'http://example.com/file19': {
                        'dir': '/man',
                        'name': 'test-1-file-9'
                    }
                },
                'depends': {
                    'dpackage-1': {
                        'version': '1.1^',
                        'type': 'required'
                    },
                    'dpackage-2': {
                        'version': '5.*',
                        'type': 'optional'
                    },
                    'dpackage-3': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            },
            '1.1.0': {
                'files': {
                    'http://example.com/file14': {
                        'dir': '/bin',
                        'name': 'test-1-file-4'
                    },
                    'http://example.com/file15': {
                        'dir': '/lib',
                        'name': 'test-1-file-5'
                    },
                    'http://example.com/file16': {
                        'dir': '/man',
                        'name': 'test-1-file-6'
                    }
                },
                'depends': {
                    'dpackage-1': {
                        'version': '1.1^',
                        'type': 'required'
                    },
                    'dpackage-2': {
                        'version': '5.*',
                        'type': 'optional'
                    },
                    'dpackage-3': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            },
            '1.0.0': {
                'files': {
                    'http://example.com/file11': {
                        'dir': '/bin',
                        'name': 'test-1-file-1'
                    },
                    'http://example.com/file12': {
                        'dir': '/lib',
                        'name': 'test-1-file-2'
                    },
                    'http://example.com/file13': {
                        'dir': '/man',
                        'name': 'test-1-file-3'
                    }
                },
                'depends': {
                    'dpackage-1': {
                        'version': '1.1^',
                        'type': 'required'
                    },
                    'dpackage-2': {
                        'version': '5.*',
                        'type': 'optional'
                    },
                    'dpackage-3': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            }
        },
        screenshots={
            'http://img.example.com/img11': 'test-1-img-1',
            'http://img.example.com/img12': 'test-1-img-2',
            'http://img.example.com/img13': 'test-1-img-3'
        }
    ).pkg

    pkg2 = ModelPackage(
        name='package-2',
        description='My second test package.',
        short_description='2 package.',
        owner='Tester',
        authors=['Tester', 'Kjers'],
        license='mylicense-2',
        tags=['xxx', 'yyy', 'ccc'],
        versions={
            '1.0.2': {
                'files': {
                    'http://example.com/file27': {
                        'dir': '/bin',
                        'name': 'test-2-file-7'
                    },
                    'http://example.com/file28': {
                        'dir': '/lib',
                        'name': 'test-2-file-8'
                    },
                    'http://example.com/file29': {
                        'dir': '/man',
                        'name': 'test-2-file-9'
                    }
                },
                'depends': {
                    'dpackage-4': {
                        'version': '1.*',
                        'type': 'required'
                    },
                    'dpackage-5': {
                        'version': '3.5.6^',
                        'type': 'optional'
                    },
                    'dpackage-6': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            },
            '1.0.1': {
                'files': {
                    'http://example.com/file24': {
                        'dir': '/bin',
                        'name': 'test-2-file-4'
                    },
                    'http://example.com/file25': {
                        'dir': '/lib',
                        'name': 'test-2-file-5'
                    },
                    'http://example.com/file26': {
                        'dir': '/man',
                        'name': 'test-2-file-6'
                    }
                },
                'depends': {
                    'dpackage-4': {
                        'version': '1.*',
                        'type': 'required'
                    },
                    'dpackage-5': {
                        'version': '3.5.6^',
                        'type': 'optional'
                    },
                    'dpackage-6': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            },
            '1.0.0': {
                'files': {
                    'http://example.com/file21': {
                        'dir': '/bin',
                        'name': 'test-2-file-1'
                    },
                    'http://example.com/file22': {
                        'dir': '/lib',
                        'name': 'test-2-file-2'
                    },
                    'http://example.com/file23': {
                        'dir': '/man',
                        'name': 'test-2-file-3'
                    }
                },
                'depends': {
                    'dpackage-4': {
                        'version': '1.*',
                        'type': 'required'
                    },
                    'dpackage-5': {
                        'version': '3.5.6^',
                        'type': 'optional'
                    },
                    'dpackage-6': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            }
        },
        screenshots={
            'http://img.example.com/img21': 'test-2-img-1',
            'http://img.example.com/img22': 'test-2-img-2',
            'http://img.example.com/img23': 'test-2-img-3'
        }
    ).pkg

    pkg3 = ModelPackage(
        name='package-3',
        description='My third test package.',
        short_description='3 package.',
        owner='Tester',
        authors=['Tester', 'Nyemst'],
        license='mylicense-3',
        tags=['aaa', 'ccc', 'zzz'],
        versions={
            '1.2.0': {
                'files': {
                    'http://example.com/file37': {
                        'dir': '/bin',
                        'name': 'test-3-file-7'
                    },
                    'http://example.com/file38': {
                        'dir': '/lib',
                        'name': 'test-3-file-8'
                    },
                    'http://example.com/file39': {
                        'dir': '/man',
                        'name': 'test-3-file-9'
                    }
                },
                'depends': {
                    'dpackage-7': {
                        'version': '1.12.51^',
                        'type': 'required'
                    },
                    'dpackage-8': {
                        'version': '3.5.*',
                        'type': 'optional'
                    },
                    'dpackage-9': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            },
            '1.1.0': {
                'files': {
                    'http://example.com/file34': {
                        'dir': '/bin',
                        'name': 'test-3-file-4'
                    },
                    'http://example.com/file35': {
                        'dir': '/lib',
                        'name': 'test-3-file-5'
                    },
                    'http://example.com/file36': {
                        'dir': '/man',
                        'name': 'test-3-file-6'
                    }
                },
                'depends': {
                    'dpackage-7': {
                        'version': '1.12.51^',
                        'type': 'required'
                    },
                    'dpackage-8': {
                        'version': '3.5.*',
                        'type': 'optional'
                    },
                    'dpackage-9': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            },
            '1.0.0': {
                'files': {
                    'http://example.com/file31': {
                        'dir': '/bin',
                        'name': 'test-3-file-1'
                    },
                    'http://example.com/file32': {
                        'dir': '/lib',
                        'name': 'test-3-file-2'
                    },
                    'http://example.com/file33': {
                        'dir': '/man',
                        'name': 'test-3-file-3'
                    }
                },
                'depends': {
                    'dpackage-7': {
                        'version': '1.12.51^',
                        'type': 'required'
                    },
                    'dpackage-8': {
                        'version': '3.5.*',
                        'type': 'optional'
                    },
                    'dpackage-9': {
                        'version': '*',
                        'type': 'recommended'
                    }
                }
            }
        },
        screenshots={
            'http://img.example.com/img31': 'test-3-img-1',
            'http://img.example.com/img32': 'test-3-img-2',
            'http://img.example.com/img33': 'test-3-img-3'
        }
    ).pkg

    def setUp(self):
        from pymongo import MongoClient

        url = 'mongodb://localhost:37017'
        if 'HEL_TESTING_MONGODB_ADDR' in os.environ:
            url = os.environ['HEL_TESTING_MONGODB_ADDR']
        self.client = MongoClient(url)
        self.db = self.client.hel
        self.db['packages'].delete_many({})
        self.db['packages'].insert_one(self.pkg1)
        del self.pkg1['_id']
        self.db['packages'].insert_one(self.pkg2)
        del self.pkg2['_id']
        self.db['packages'].insert_one(self.pkg3)
        del self.pkg3['_id']

        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        self.db['packages'].delete_many({})
        self.client.close()

    @one_value_param('name')
    def test_pkg_search_name(self):
        return [
            ('package', [self.pkg1, self.pkg2, self.pkg3],),
            ('1', [self.pkg1],)
        ]

    @one_value_param('description')
    def test_pkg_search_description(self):
        return [
            ('[Mm]y', [self.pkg1, self.pkg2, self.pkg3],),
            ('first', [self.pkg1],),
            ('second', [self.pkg2],),
            ('third', [self.pkg3],),
            ('test', [self.pkg1, self.pkg2, self.pkg3],)
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
            ('[Tt]ester', [self.pkg1, self.pkg2, self.pkg3],),
            ('Kjers', [self.pkg2],)
        ]

    @one_value_param('screen_desc')
    def test_pkg_search_screen_desc(self):
        return [
            ('3', [self.pkg1, self.pkg2, self.pkg3],),
            ('test-3', [self.pkg3],)
        ]

    @param('license')
    def test_pkg_search_license(self):
        return [
            (['mylicense-1'], [self.pkg1],),
            (['mylicense-2', 'mylicense-3'], [self.pkg2, self.pkg3],)
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
            (['http://example.com/file11'], [self.pkg1],),
            (['http://example.com/file31'], [self.pkg3],),
            (['http://example.com/file22',
              'http://example.com/file23'], [self.pkg2],),
            (['http://example.com/file12',
              'http://example.com/file32'], [],)
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
            (['test-2-file-2', 'test-2-file-3'], [self.pkg2],),
            (['test-1-file-1', 'test-1-file-2'], [self.pkg1],),
        ]

    @param('dependency')
    def test_pkg_search_dependency(self):
        return [
            (['dpackage-8:3.5.*'], [self.pkg3],),
            (['dpackage-1:6.6.6:recommended'], [],),
            (['dpackage-2'], [self.pkg1],)
        ]

    @param('screen_url')
    def test_pkg_search_screen_url(self):
        return [
            (['http://img.example.com/img11',
              'http://img.example.com/img31'], [self.pkg1, self.pkg3],),
            (['http://img.example.com/img21',
              'http://img.example.com/img23'], [self.pkg2],),
            (['http://img.example.com/img42'], [],)
        ]
