from pyramid.httpexceptions import HTTPBadRequest
import rfc3987

from hel.utils import parse_search_phrase, jexc
from hel.utils.constants import Constants
from hel.utils.messages import Messages
from hel.utils.version import latest_version


def _only_one_param(func):
    func._only_one = True
    return func


class PackagesSearchParams:

    @_only_one_param
    def name(param):
        """Search by name"""

        def search(pkg):
            success = True
            phrases = parse_search_phrase(param)
            for phrase in phrases:
                if phrase not in pkg['name']:
                    success = False
                    break
            return success

        return search

    @_only_one_param
    def description(param):
        """Search by description"""

        def search(pkg):
            success = True
            phrases = parse_search_phrase(param)
            for phrase in phrases:
                if phrase not in pkg['description']:
                    success = False
                    break
            return success

        return search

    @_only_one_param
    def short_description(param):
        def search(pkg):
            success = True
            phrases = parse_search_phrase(param)
            for phrase in phrases:
                if phrase not in pkg['short_description']:
                    success = False
                    break
            return success

        return search

    @_only_one_param
    def authors(param):
        """Search by author name"""

        def search(pkg):
            success = True
            phrases = parse_search_phrase(param)
            for phrase in phrases:
                success_loop = False
                for author in pkg['authors']:
                    if phrase in author:
                        success_loop = True
                        break
                if not success_loop:
                    success = False
                    break
            return success

        return search

    @_only_one_param
    def license(param):
        """Search by license"""

        def search(pkg):
            return param in pkg['license']

        return search

    def tags(param):
        """Search by tag.

        Logical AND is used to concatenate params.
        """

        def search(pkg):
            success = True
            for exp_tag in param:
                success_loop = False
                for tag in pkg['tags']:
                    if exp_tag == tag:
                        success_loop = True
                        break
                if not success_loop:
                    success = False
                    break
            return success

        return search

    def file_url(param):
        """Search by file URL.

        Logical AND is used to concatenate params.
        """

        def search(pkg):
            success = True
            ver = pkg['versions'][str(latest_version(pkg))]
            for url in param:
                if url not in ver['files']:
                    success = False
                    break
            return success

        return search

    def file_dir(param):
        """Search by directory.

        Logical AND is used to concatenate params.
        """

        def search(pkg):
            success = True
            ver = pkg['versions'][str(latest_version(pkg))]
            for d in param:
                success_loop = False
                for k, v in ver['files'].items():
                    if v['dir'] == d:
                        success_loop = True
                        break
                if not success_loop:
                    success = False
                    break
            return success

        return search

    def file_name(param):
        """Search by file name.

        Logical AND is used to concatenate params.
        """

        def search(pkg):
            success = True
            ver = pkg['versions'][str(latest_version(pkg))]
            for name in param:
                success_loop = False
                for k, v in ver['files'].items():
                    if v['name'] == name:
                        success_loop = True
                        break
                if not success_loop:
                    success = False
                    break
            return success

        return search

    def dependency(param):
        """Returns packages depending on specific packages.

        Param format: <name>[:<version>[:<type>]]
        Logical AND is used to concatenate params.
        """

        def search(pkg):
            success = True
            ver = pkg['versions'][str(latest_version(pkg))]
            for dep_info in param:
                dep = dep_info.split(':')
                name = dep[0]
                if len(dep) > 2:
                    dep_type = dep[2]
                if len(dep) > 1:
                    version = dep[1]
                if name not in ver['depends']:
                    success = False
                else:
                    if (len(dep) > 2 and
                            ver['depends'][name]
                            ['version'] != version):
                        success = False
                    else:
                        if (len(dep) > 2 and
                                ver['depends'][name]
                                ['type'] != dep_type):
                            success = False
            return success

        return search

    def screen_url(param):
        """Search by screenshot URL.

        Logical AND is used to concatenate params.
        """

        def search(pkg):
            success = True
            for url in param:
                if url not in pkg['screenshots']:
                    success = False
            return success

        return search

    @_only_one_param
    def screen_desc(param):
        """Search by screenshot description"""

        def search(pkg):
            success = True
            phrases = parse_search_phrase(param)
            for phrase in phrases:
                success_loop = False
                for k, v in pkg['screenshots'].items():
                    if phrase in v:
                        success_loop = True
                        break
                if not success_loop:
                    success = False
                    break
            return success

        return search


class PackagesSearcher:

    def __init__(self, params):
        self.params = params

    def __call__(self):
        searchers = []
        for param_name, param in self.params.items():
            if hasattr(PackagesSearchParams, param_name):
                param_method = getattr(PackagesSearchParams, param_name)
                if (not hasattr(param_method, '_no_param') and
                        (len(param) == 0 or param[0] == '')):
                    jexc(HTTPBadRequest, Messages.no_values % param_name)
                if hasattr(param_method, '_only_one'):
                    if len(param) > 1:
                        jexc(HTTPBadRequest, Messages.too_many_values % (
                             1, len(param),))
                    else:
                        param = param[0]
                search = param_method(param)
                searchers.append(search)
            else:
                jexc(HTTPBadRequest, Messages.bad_search_param % param_name)
        self.searchers = searchers
        return searchers

    def search(self, pkgs):
        packages = []
        for pkg in pkgs:
            packages.append(
                replace_chars_in_keys(
                    pkg, Constants.key_replace_char, '.'))
        result = []
        for pkg in packages:
            success = True
            for searcher in self.searchers:
                if not searcher(pkg):
                    success = False
                    break
            if success:
                result.append(pkg)
        return result


def check(value, expected_type, message=None):
    if type(value) != expected_type:
        jexc(HTTPBadRequest, message)
    return value


def check_list_of_strs(value, message=None):
    check(value, list, message)
    for item in value:
        if type(item) != str:
            jexc(HTTPBadRequest, message)
    return value


def replace_chars_in_keys(d, repl_chr, repl_to):
    try:
        result = {}
        for k, v in d.items():
            result[k.replace(repl_chr, repl_to)] = replace_chars_in_keys(
                v, repl_chr, repl_to)
    except (ValueError, TypeError, AttributeError):
        return d
    return result


def parse_url(url):
    try:
        matches = rfc3987.parse(url, rule='URI')
    except ValueError:
        jexc(HTTPBadRequest, Messages.invalid_uri)
    if matches['scheme'] not in ['http', 'https']:
        jexc(HTTPBadRequest, Messages.invalid_uri)
    matches['path'] = matches['path'] or '/'
    matches['fragment'] = None
    return rfc3987.compose(**matches)
