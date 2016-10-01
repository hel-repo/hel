import json
import unittest

from pyramid.httpexceptions import HTTPBadRequest

from hel.utils.messages import Messages


class UnitTests(unittest.TestCase):

    def test_are_equal(self):
        from hel.utils.tests import are_equal
        self.assertTrue(are_equal([{
                'test': 'hi',
                'test2': ['test3', 'test2', 'test1']
            }], [{
                'test2': ['test3', 'test2', 'test1'],
                'test': 'hi'
            }]))
        self.assertFalse(are_equal([{
                'test': 'hi',
                'test2': ['test1', 'test2']
            }], [{
                'test2': ['test1', 'test2', 'test3']
            }]))
        self.assertFalse(are_equal([{
                'test': 'hi'
            }], [{
                'test': 'test'
            }]))

    def test_check_list_of_strs(self):
        from hel.utils.query import check_list_of_strs
        try:
            check_list_of_strs(['test', 555], 'test')
        except HTTPBadRequest as e:
            self.assertEqual(json.loads(e.body.decode('utf-8'))['message'],
                             'test')
        else:
            raise AssertionError()
        check_list_of_strs(['test', 'test2'])

    def test_pkg_model(self):
        from hel.utils.models import ModelPackage
        from hel.utils.tests.sample_packages import pkg1
        pkg = pkg1.data
        pkg['versions']['1.0.0']['depends']['dpackage-2']['type'] = 'hi'
        try:
            ModelPackage(**pkg)
        except ValueError as e:
            self.assertEqual(str(e), Messages.wrong_dep_type)
        else:
            raise AssertionError()
        json.loads(pkg1.json)

    def test_resource(self):
        from hel.resources import Resource
        self.assertEqual(Resource.__repr__(Resource),
                         object.__repr__(Resource))
