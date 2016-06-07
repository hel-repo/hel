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


def one_param(name):

    def wrap(func):

        def f(self):
            tests = func(self)

            # 0 values: should fail
            with self.subTest(test='0 values'):
                try:
                    search_query = PackagesSearchQuery({
                        name: []
                    })()
                except HTTPBadRequest as e:
                    if str(e) == Messages.no_values % name:
                        # Expected exception
                        pass
                    else:
                        raise e
                else:
                    raise e

            # 2, 3 values: should fail
            for i in range(2, 4):
                with self.subTest(test='%s values' % i):
                    try:
                        search_query = PackagesSearchQuery({
                            name: ['hel'] * i
                        })()
                    except HTTPBadRequest as e:
                        if str(e) == Messages.too_many_values % (1, i):
                            # Expected exception
                            pass
                        else:
                            raise e
                    else:
                        raise e

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
                    # self.assertTrue(are_equal(search_result, expected))

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
        versions=[
            {
                'number': '1.1.1',
                'files': [
                    {
                        'url': 'http://example.com/file17',
                        'dir': '/bin',
                        'name': 'test-1-file-7'
                    },
                    {
                        'url': 'http://example.com/file18',
                        'dir': '/lib',
                        'name': 'test-1-file-8'
                    },
                    {
                        'url': 'http://example.com/file19',
                        'dir': '/man',
                        'name': 'test-1-file-9'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-1',
                        'version': '1.1^',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-2',
                        'version': '5.*',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-3',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            },
            {
                'number': '1.1.0',
                'files': [
                    {
                        'url': 'http://example.com/file14',
                        'dir': '/bin',
                        'name': 'test-1-file-4'
                    },
                    {
                        'url': 'http://example.com/file15',
                        'dir': '/lib',
                        'name': 'test-1-file-5'
                    },
                    {
                        'url': 'http://example.com/file16',
                        'dir': '/man',
                        'name': 'test-1-file-6'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-1',
                        'version': '1.1^',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-2',
                        'version': '5.*',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-3',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            },
            {
                'number': '1.0.0',
                'files': [
                    {
                        'url': 'http://example.com/file11',
                        'dir': '/bin',
                        'name': 'test-1-file-1'
                    },
                    {
                        'url': 'http://example.com/file12',
                        'dir': '/lib',
                        'name': 'test-1-file-2'
                    },
                    {
                        'url': 'http://example.com/file13',
                        'dir': '/man',
                        'name': 'test-1-file-3'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-1',
                        'version': '1.1^',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-2',
                        'version': '5.*',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-3',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            }
        ],
        screenshots=[
            {
                'url': 'http://img.example.com/img11',
                'description': 'test-1-img-1'
            },
            {
                'url': 'http://img.example.com/img12',
                'description': 'test-1-img-2'
            },
            {
                'url': 'http://img.example.com/img13',
                'description': 'test-1-img-3'
            }
        ]
    ).data

    pkg2 = ModelPackage(
        name='package-2',
        description='My second test package.',
        short_description='2 package.',
        owner='Tester',
        authors=['Tester', 'Kjers'],
        license='mylicense-2',
        tags=['xxx', 'yyy', 'ccc'],
        versions=[
            {
                'number': '1.0.2',
                'files': [
                    {
                        'url': 'http://example.com/file27',
                        'dir': '/bin',
                        'name': 'test-2-file-7'
                    },
                    {
                        'url': 'http://example.com/file28',
                        'dir': '/lib',
                        'name': 'test-2-file-8'
                    },
                    {
                        'url': 'http://example.com/file29',
                        'dir': '/man',
                        'name': 'test-2-file-9'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-4',
                        'version': '1.*',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-5',
                        'version': '3.5.6^',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-6',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            },
            {
                'number': '1.0.1',
                'files': [
                    {
                        'url': 'http://example.com/file24',
                        'dir': '/bin',
                        'name': 'test-2-file-4'
                    },
                    {
                        'url': 'http://example.com/file25',
                        'dir': '/lib',
                        'name': 'test-2-file-5'
                    },
                    {
                        'url': 'http://example.com/file26',
                        'dir': '/man',
                        'name': 'test-2-file-6'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-4',
                        'version': '1.*',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-5',
                        'version': '3.5.6^',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-6',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            },
            {
                'number': '1.0.0',
                'files': [
                    {
                        'url': 'http://example.com/file21',
                        'dir': '/bin',
                        'name': 'test-2-file-1'
                    },
                    {
                        'url': 'http://example.com/file22',
                        'dir': '/lib',
                        'name': 'test-2-file-2'
                    },
                    {
                        'url': 'http://example.com/file23',
                        'dir': '/man',
                        'name': 'test-2-file-3'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-4',
                        'version': '1.*',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-5',
                        'version': '3.5.6^',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-6',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            }
        ],
        screenshots=[
            {
                'url': 'http://img.example.com/img21',
                'description': 'test-2-img-1'
            },
            {
                'url': 'http://img.example.com/img22',
                'description': 'test-2-img-2'
            },
            {
                'url': 'http://img.example.com/img23',
                'description': 'test-2-img-3'
            }
        ]
    ).data

    pkg3 = ModelPackage(
        name='package-3',
        description='My third test package.',
        short_description='3 package.',
        owner='Tester',
        authors=['Tester', 'Nyemst'],
        license='mylicense-3',
        tags=['aaa', 'ccc', 'zzz'],
        versions=[
            {
                'number': '1.2.0',
                'files': [
                    {
                        'url': 'http://example.com/file37',
                        'dir': '/bin',
                        'name': 'test-3-file-7'
                    },
                    {
                        'url': 'http://example.com/file38',
                        'dir': '/lib',
                        'name': 'test-3-file-8'
                    },
                    {
                        'url': 'http://example.com/file39',
                        'dir': '/man',
                        'name': 'test-3-file-9'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-7',
                        'version': '1.12.51^',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-8',
                        'version': '3.5.*',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-9',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            },
            {
                'number': '1.1.0',
                'files': [
                    {
                        'url': 'http://example.com/file34',
                        'dir': '/bin',
                        'name': 'test-3-file-4'
                    },
                    {
                        'url': 'http://example.com/file35',
                        'dir': '/lib',
                        'name': 'test-3-file-5'
                    },
                    {
                        'url': 'http://example.com/file36',
                        'dir': '/man',
                        'name': 'test-3-file-6'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-7',
                        'version': '1.12.51^',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-8',
                        'version': '3.5.*',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-9',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            },
            {
                'number': '1.0.0',
                'files': [
                    {
                        'url': 'http://example.com/file31',
                        'dir': '/bin',
                        'name': 'test-3-file-1'
                    },
                    {
                        'url': 'http://example.com/file32',
                        'dir': '/lib',
                        'name': 'test-3-file-2'
                    },
                    {
                        'url': 'http://example.com/file33',
                        'dir': '/man',
                        'name': 'test-3-file-3'
                    }
                ],
                'depends': [
                    {
                        'name': 'dpackage-7',
                        'version': '1.12.51^',
                        'type': 'required'
                    },
                    {
                        'name': 'dpackage-8',
                        'version': '3.5.*',
                        'type': 'optional'
                    },
                    {
                        'name': 'dpackage-9',
                        'version': '*',
                        'type': 'recommended'
                    }
                ]
            }
        ],
        screenshots=[
            {
                'url': 'http://img.example.com/img31',
                'description': 'test-3-img-1'
            },
            {
                'url': 'http://img.example.com/img32',
                'description': 'test-3-img-2'
            },
            {
                'url': 'http://img.example.com/img33',
                'description': 'test-3-img-3'
            }
        ]
    ).data

    def setUp(self):
        from pymongo import MongoClient

        self.client = MongoClient('mongodb://localhost:37017')
        self.db = self.client.hel
        self.db['packages'].delete_many({})
        for pkg in [self.pkg1, self.pkg2, self.pkg3]:
            self.db['packages'].insert_one(pkg)
            del pkg['_id']

        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        self.db['packages'].delete_many({})
        self.client.close()

    @one_param('name')
    def test_list_name(self):
        return [
            ('package', [self.pkg1, self.pkg2, self.pkg3],),
            ('1', [self.pkg1],)
        ]
