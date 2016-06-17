from pyramid.httpexceptions import HTTPBadRequest

from hel.utils.messages import Messages


def _only_one_param(func):
    func._only_one = True
    return func


def concat_params(params, op='or'):
    operator = '$' + op
    if len(params) > 1:
        return {operator: [x for x in params]}
    elif len(params) == 1:
        return params[0]
    else:
        raise ValueError


class PackagesSearchParams:
    """Provides methods for converting GET-params to MongoDB query"""

    @_only_one_param
    def name(param):
        """Search by name regex"""

        return {'name': {'$regex': '.*' + str(param) + '.*'}}

    @_only_one_param
    def description(param):
        """Search by description regex"""

        return {'description': {'$regex': '.*' + str(param) + '.*'}}

    @_only_one_param
    def short_description(param):
        return {'short_description': {'$regex': '.*' + str(param) + '.*'}}

    @_only_one_param
    def authors(param):
        """Search by author name regex"""

        return {'authors': {'$regex': '.*' + str(param) + '.*'}}

    def license(param):
        """Search by license.

        Logical OR is used to concatenate params.
        """

        return {'license': {'$in': [str(x) for x in param]}}

    def tags(param):
        """Search by tag.

        Logical AND is used to concatenate params.
        """

        return {'tags': concat_params([str(x) for x in param], 'all')}

    def file_url(param):
        """Search by file URL.

        Logical AND is used to concatenate params.
        """

        return {'versions.files.url': concat_params([str(x) for x in param],
                'all')}

    def file_dir(param):
        """Search by directory.

        Logical AND is used to concatenate params.
        """

        return {'versions.files.dir': concat_params([str(x) for x in param],
                'all')}

    def file_name(param):
        """Search by file name.

        Logical AND is used to concatenate params.
        """

        return {'versions.files.name': concat_params([str(x) for x in param],
                'all')}

    def dependency(param):
        """Returns packages depending on specific packages.

        Param format: <name>[:<version>[:<type>]]
        Logical OR is used to concatenate params.
        """

        search_query = []
        for dep in param:
            dep_full = str(dep).split(':')
            if len(dep_full) == 2:
                dep_full.append(None)
            elif len(dep_full) == 1:
                dep_full.append(None)
                dep_full.append(None)

            append_list = [{'versions.depends.name': dep_full[0]}]
            if dep_full[1]:
                append_list.append({'versions.depends.version': dep_full[1]})
            if dep_full[2]:
                append_list.append({'versions.depends.type': dep_full[2]})

            search_query.append({'$and': append_list})
        return concat_params(search_query)

    def screen_url(param):
        """Search by screenshot URL.

        Logical OR is used to concatenate params.
        """

        return {'screenshots.url': {'$in': [str(x) for x in param]}}

    @_only_one_param
    def screen_desc(param):
        """Search by screenshot description regex"""

        return {'screenshots.description': {
            '$regex': '.*' + str(param) + '.*'
        }}


class PackagesSearchQuery:

    def __init__(self, params):
        self.params = params

    def __call__(self):
        query = {}
        for param_name, param in self.params.items():
            if hasattr(PackagesSearchParams, param_name):
                param_method = getattr(PackagesSearchParams, param_name)
                if (not hasattr(param_method, '_no_param') and
                        (len(param) == 0 or param[0] == '')):
                    raise HTTPBadRequest(
                        detail=Messages.no_values % param_name)
                if hasattr(param_method, '_only_one'):
                    if len(param) > 1:
                        raise HTTPBadRequest(
                            detail=Messages.too_many_values % (
                                1, len(param),))
                    else:
                        param = param[0]
                search_doc = param_method(param)
                for k, v in search_doc.items():
                    query[k] = v
            else:
                raise HTTPBadRequest(
                    detail=Messages.bad_search_param % param_name)
        self.query = query
        return query

    def __tostring__(self):
        self.__call__()
        return str(self.query)


def check(value, expected_type, message=None):
    if type(value) != expected_type:
        raise HTTPBadRequest(detail=message)
    return value


def check_list_of_strs(value, message=None):
    check(value, list, message)
    for item in value:
        if type(item) != str:
            raise HTTPBadRequest(detail=message)
    return value
