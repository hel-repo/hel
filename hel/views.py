import copy
import datetime
import hashlib
import logging
import os

from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPNotFound,
    HTTPSuccessful,
    HTTPError,
    HTTPNoContent,
    HTTPOk,
    HTTPCreated,
    HTTPInternalServerError
)
from pyramid.request import Request
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import view_config
import semantic_version as semver

from hel.resources import Package, Packages, User, Users
from hel.utils.constants import Constants
from hel.utils.messages import Messages
from hel.utils.models import ModelPackage, ModelUser
from hel.utils.query import (
    PackagesSearcher,
    check,
    check_list_of_strs,
    parse_url,
    replace_chars_in_keys
)


log = logging.getLogger(__name__)


# Exception views
@view_config(context=HTTPSuccessful, renderer='json')
def exc_success(exc, request):
    request.response.status = exc.code
    request.response.headers.extend(exc.headers)
    if exc.empty_body:
        return request.response
    else:
        body = exc.body
        if type(body) == bytes:
            body = body.decode('utf-8')
        return {"success": True,
                "title": exc.title,
                "data": body,
                "code": exc.code,
                "version": request.version,
                "logged_in": request.logged_in}


@view_config(context=HTTPError, renderer='json')
def exc_error(exc, request):
    request.response.status = exc.code
    request.response.headers.extend(exc.headers)
    return {"success": False,
            "title": exc.title,
            "message": exc.detail,
            "explanation": exc.explanation,
            "code": exc.code,
            "version": request.version,
            "logged_in": request.logged_in}


# Auth controller
@view_config(route_name='auth')
def auth(request):
    nickname = ''
    password = ''
    email = ''
    try:
        params = request.json_body
    except:
        raise HTTPBadRequest(detail=Messages.bad_request)
    if 'action' not in params:
        message = Messages.bad_request
    elif request.logged_in:
        nickname = request.authenticated_userid
        if params['action'] == 'log-out':
            headers = forget(request)
            raise HTTPOk(body=Messages.logged_out, headers=headers)
        raise HTTPNoContent()
    elif params['action'] == 'log-in':
        try:
            nickname = params['nickname'].strip()
            password = params['password'].strip()
        except KeyError:
            raise HTTPBadRequest(detail=Messages.bad_request)
        if nickname == '':
            raise HTTPBadRequest(detail=Messages.empty_nickname)
        if password == '':
            raise HTTPBadRequest(detail=Messages.empty_password)
        pass_hash = hashlib.sha512(password.encode()).hexdigest()
        user = request.db['users'].find_one({'nickname': nickname})
        if not user:
            raise HTTPBadRequest(detail=Messages.failed_login)
        correct_hash = user['password']
        if pass_hash != correct_hash:
            raise HTTPBadRequest(detail=Messages.failed_login)
        headers = remember(request, nickname)
        raise HTTPOk(body=Messages.logged_in, headers=headers)
    elif params['action'] == 'register':
        try:
            nickname = params['nickname'].strip()
            email = params['email'].strip()
            password = params['password'].strip()
        except (KeyError, AttributeError):
            raise HTTPBadRequest(detail=Messages.bad_request)
        if nickname == '':
            raise HTTPBadRequest(detail=Messages.empty_nickname)
        if email == '':
            raise HTTPBadRequest(detail=Messages.empty_email)
        if password == '':
            raise HTTPBadRequest(detail=Messages.empty_password)
        pass_hash = hashlib.sha512(password.encode()).hexdigest()
        user = request.db['users'].find_one({'nickname': nickname})
        if user:
            raise HTTPBadRequest(detail=Messages.nickname_in_use)
        user = request.db['users'].find_one({'email': email})
        if user:
            raise HTTPBadRequest(detail=Messages.email_in_use)
        act_phrase = ''.join('{:02x}'.format(x) for x in os.urandom(
            request.registry.settings
            ['activation.length']))
        act_till = (datetime.datetime.now() + datetime.timedelta(
            seconds=request.registry.settings['activation.time']))
        subrequest = Request.blank('/users', method='POST', POST=(
                str(ModelUser(nickname=nickname,
                              email=email,
                              password=pass_hash,
                              activation_phrase=act_phrase,
                              activation_till=act_till))),
            content_type='application/json')
        subrequest.no_permission_check = True
        response = request.invoke_subrequest(subrequest, use_tweens=True)
        if response.status_code == 201:
            # TODO: send activation email
            raise HTTPOk(body=Messages.account_created_success)
        else:  # pragma: no cover
            log.error(
                'Could not create a user: subrequest'
                ' returned with status code %s!\n'
                'Local variables in frame:%s',
                response.status_code,
                ''.join(['\n * ' + str(x) + ' = ' + str(y)
                         for x, y in locals().items()])
            )
            raise HTTPInternalServerError(Messages.internal_error)
    raise HTTPBadRequest(detail=Messages.bad_request)


# Package controller
@view_config(request_method='PATCH',
             context=Package,
             permission='pkg_update')
def update_package(context, request):
    query = {}
    old = replace_chars_in_keys(
        context.retrieve(), Constants.key_replace_char, '.')
    for k, v in request.json_body.items():
        if k == 'name':
            check(v, str, Messages.type_mismatch % (k, 'str',))
            if len([x for x in (request.db['packages']
                                .find({'name': v}))]) > 0:
                raise HTTPConflict(detail=Messages.pkg_name_conflict)
            if not Constants.name_pattern.match(v):
                raise HTTPBadRequest(detail=Messages.pkg_bad_name)
        elif k in ['description', 'license']:
            query[k] = check(
                v, str,
                Messages.type_mismatch % (k, 'str',))
        elif k == 'short_description':
            query[k] = check(
                v, str,
                Messages.type_mismatch % (k, 'str',))[:120]
        elif k == 'owners':
            check_list_of_strs(
                v, Messages.type_mismatch % (k, 'list of strs',))
            for owner in v:
                if not Constants.user_pattern.match(owner):
                    raise HTTPBadRequest(detail=Messages.user_bad_name)
            if len(v) == 0:
                raise HTTPBadRequest(detail=Messages.empty_owner_list)
            query[k] = v
        elif k in ['authors', 'tags']:
            query[k] = check_list_of_strs(
                v, Messages.type_mismatch % (k, 'list of strs',))
        elif k == 'versions':
            check(
                v, dict,
                Messages.type_mismatch % (k, 'dict',))
            for n, ver in v.items():
                try:
                    num = str(semver.Version.coerce(n))
                except ValueError as e:
                    raise HTTPBadRequest(detail=str(e))
                if ver is None:
                    if k not in query:
                        query[k] = {}
                    query[k][num] = None
                else:
                    check(
                        ver, dict,
                        Messages.type_mismatch % ('version_info', 'dict',))
                    if num not in old['versions']:
                        if ('depends' not in ver or
                                'files' not in ver or
                                'changes' not in ver):
                            raise HTTPBadRequest(detail=Messages.partial_ver)
                        else:
                            if k not in query:
                                query[k] = {}
                            if num not in query[k]:
                                query[k][num] = {}
                            if 'files' not in query[k][num]:
                                query[k][num]['files'] = {}
                            if 'depends' not in query[k][num]:
                                query[k][num]['depends'] = {}
                            if 'changes' not in query[k][num]:
                                query[k][num]['changes'] = ""
                    if 'files' in ver:
                        check(
                            ver['files'], dict,
                            Messages.type_mismatch % ('files', 'dict',))
                        for unchecked_url, file_info in ver['files'].items():
                            url = parse_url(unchecked_url)
                            if file_info is None:
                                if k not in query:
                                    query[k] = {}
                                if num not in query[k]:
                                    query[k][num] = {}
                                if 'files' not in query[k][num]:
                                    query[k][num]['files'] = {}
                                query[k][num]['files'][url] = None
                            else:
                                check(
                                    file_info, dict,
                                    Messages.type_mismatch % (
                                        'file_info', 'dict',))
                                if ((num not in old['versions'] or
                                        url not in old['versions'][num]
                                        ['files']) and
                                        ('dir' not in file_info or
                                         'name' not in file_info)):
                                    raise HTTPBadRequest(
                                        detail=Messages.partial_ver
                                    )
                                if ('dir' in file_info and
                                        check(
                                            file_info['dir'], str,
                                            Messages.type_mismatch % (
                                                'file_dir', 'str',)) or
                                        'name' in file_info and
                                        check(
                                            file_info['name'], str,
                                            Messages.type_mismatch % (
                                                'file_name', 'str',))):
                                    if k not in query:
                                        query[k] = {}
                                    if num not in query[k]:
                                        query[k][num] = {}
                                    if 'files' not in query[k][num]:
                                        query[k][num]['files'] = {}
                                    if url not in query[k][num]['files']:
                                        (query[k][num]['files']
                                         [url]) = {}
                                if 'dir' in file_info:
                                    (query[k][num]['files']
                                     [url]['dir']) = file_info['dir']
                                if 'name' in file_info:
                                    (query[k][num]['files']
                                     [url]['name']) = file_info['name']

                    if 'depends' in ver:
                        check(
                            ver['depends'], dict,
                            Messages.type_mismatch % ('depends', 'dict',))
                        for dep_name, dep_info in ver['depends'].items():
                            check(
                                dep_info, dict,
                                Messages.type_mismatch % (
                                    'dep_info', 'dict',))
                            if dep_info:
                                if ((num not in old['versions'] or
                                        dep_name not in old['versions'][num]
                                        ['depends']) and
                                        ('version' not in dep_info or
                                         'type' not in dep_info)):
                                    raise HTTPBadRequest(
                                        detail=Messages.partial_ver
                                    )
                                if k not in query:
                                    query[k] = {}
                                if num not in query[k]:
                                    query[k][num] = {}
                                if ('version' in dep_info or
                                        'type' in dep_info):
                                    if 'version' in dep_info:
                                        check(
                                            dep_info['version'], str,
                                            Messages.type_mismatch % (
                                                'dep_version', 'str',))
                                        try:
                                            semver.Spec(dep_info['version'])
                                        except ValueError as e:
                                            raise HTTPBadRequest(detail=str(e))
                                    if 'type' in dep_info:
                                        check(
                                            dep_info['type'], str,
                                            Messages.type_mismatch % (
                                                'dep_type', 'str',))
                                        if dep_info['type'] not in [
                                                    'recommended',
                                                    'optional',
                                                    'required'
                                                ]:
                                            raise HTTPBadRequest(
                                                detail=Messages.wrong_dep_type
                                            )
                                    if 'depends' not in query[k][num]:
                                        query[k][num]['depends'] = {}
                                    if (dep_name not in
                                            query[k][num]['depends']):
                                        (query[k][num]['depends']
                                         [dep_name]) = {}
                                if 'version' in dep_info:
                                    (query[k][num]['depends']
                                     [dep_name]['version']) = (
                                        dep_info['version'])
                                if 'type' in dep_info:
                                    (query[k][num]['depends']
                                     [dep_name]['type']) = dep_info['type']
                    if 'changes' in ver:
                        check(ver['changes'], str,
                              Messages.type_mismatch % ('changes', 'str',))
                        if k not in query:
                            query[k] = {}
                        if num not in query[k]:
                            query[k][num] = {}
                        query[k][num]['changes'] = ver['changes']
        elif k == 'screenshots':
            check(v, dict, Messages.type_mismatch % (k, 'dict',))
            for unchecked_url, desc in v.items():
                url = parse_url(unchecked_url)
                if (desc is None or
                        type(check(
                            desc, str,
                            Messages.type_mismatch % (
                                'screenshot_desc', 'str',))) == str):
                    if k not in query:
                        query[k] = {}
                    query[k][url] = desc

    query.setdefault('stats', {}).setdefault('date', {})['last-updated'] = (
            datetime.datetime.utcnow().strftime(Constants.date_format))

    def r(d, nd):
        if type(d) == dict and type(nd) == dict:
            result = copy.copy(d)
            for k, v in nd.items():
                if k in d:
                    data = r(d[k], v)
                    if data is not None:
                        result[k] = data
                    else:
                        del result[k]
                else:
                    if v is not None:
                        result[k] = v
            return result
        else:
            return nd

    query = r(old, query)
    query = replace_chars_in_keys(query, '.', Constants.key_replace_char)
    context.update(query, True)

    raise HTTPNoContent()


@view_config(request_method='GET',
             context=Package,
             permission='pkg_view')
def get_package(context, request):
    r = context.retrieve()

    if r is None:
        raise HTTPNotFound()
    else:
        context.update({
            '$inc': {
                'stats.views': 1
            }
        })
        context.update({
            '$unset': {
                'stats.downloads': ""
            }
        })
        del r['_id']
        raise HTTPOk(
            body=replace_chars_in_keys(r, Constants.key_replace_char, '.'))


@view_config(request_method='DELETE',
             context=Package,
             permission='pkg_delete')
def delete_package(context, request):
    context.delete()

    raise HTTPNoContent()


@view_config(request_method='POST',
             context=Packages,
             permission='pkg_create')
def create_package(context, request):
    try:
        data = copy.deepcopy(request.json_body)
        if 'owners' not in data:
            data['owners'] = [request.authenticated_userid[1:]]
        pkg = ModelPackage(True, **data)
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        raise HTTPBadRequest(detail=Messages.bad_package % str(e))
    except HTTPBadRequest:
        raise
    except Exception as e:  # pragma: no cover
        log.warn('Exception caught in create_package: %r.', e)
        raise HTTPBadRequest(detail=Messages.bad_package % "'unknown'")
    if len([x for x in (request.db['packages']
                        .find({'name': pkg.data['name']}))]) > 0:
        raise HTTPConflict(detail=Messages.pkg_name_conflict)
    if not Constants.name_pattern.match(pkg.data['name']):
        raise HTTPBadRequest(detail=Messages.pkg_bad_name)
    data = pkg.pkg
    context.create(data)

    raise HTTPCreated()


@view_config(request_method='GET',
             context=Packages,
             permission='pkgs_view')
def list_packages(context, request):
    params = request.GET.dict_of_lists()
    offset = 0
    length = request.registry.settings['controllers.packages.list_length']
    if 'offset' in params:
        offset = params.pop('offset')[0]
    try:
        offset = int(offset)
    except ValueError:
        offset = 0
    searcher = PackagesSearcher(params)
    searcher()
    packages = context.retrieve({})
    found = searcher.search(packages)
    result_list = found[offset:offset+length]
    for v in result_list:
        if '_id' in v:
            del v['_id']

    result = {
        'offset': offset,
        'total': len(found),
        'sent': len(result_list),
        'truncated': (len(found) > request.registry.settings
                      ['controllers.packages.list_length']),
        'list': result_list
    }
    raise HTTPOk(body=result)


# User controller
@view_config(request_method='PATCH',
             context=User,
             permission='user_update')
def update_user(context, request):
    context.update(request.json_body, True)

    raise HTTPNoContent()


@view_config(request_method='GET',
             context=User,
             permission='user_get')
def get_user(context, request):
    r = context.retrieve()

    if r is None:
        raise HTTPNotFound()
    else:
        data = {
            'nickname': r['nickname'],
            'groups': r['groups']
        }
        raise HTTPOk(body=data)


@view_config(request_method='DELETE',
             context=User,
             permission='user_delete')
def delete_user(context, request):
    context.delete()

    raise HTTPNoContent()


@view_config(request_method='POST',
             context=Users,
             permission='user_create')
def create_user(context, request):
    try:
        user = ModelUser(True, **request.json_body)
    except:
        raise HTTPBadRequest(detail=Messages.bad_user)
    context.create(user.data)

    raise HTTPCreated()


@view_config(request_method='GET',
             context=Users,
             permission='user_list')
def list_users(context, request):
    params = request.GET
    offset = 0
    length = request.registry.settings['controllers.users.list_length']
    if 'offset' in params:
        offset = params.pop('offset')[0]
    try:
        offset = int(offset)
    except:
        offset = 0
    params = params.dict_of_lists()
    groups = None
    if 'groups' in params:
        groups = params['groups']
    retrieved_raw = context.retrieve()
    retrieved = []
    if groups:
        for v in retrieved_raw:
            success = True
            for group_query in groups:
                success_loop = False
                for group in v['groups']:
                    if group_query == group:
                        success_loop = True
                        break
                if not success_loop:
                    success = False
                    break
            if success:
                retrieved.append(v)
    else:
        retrieved = retrieved_raw
    res = retrieved[offset:offset+length]
    result_list = []
    for v in res:
        result_list.append({
                'nickname': v['nickname'],
                'groups': v['groups']
            })

    result = {
        'offset': offset,
        'total': len(retrieved),
        'sent': len(result_list),
        'truncated': (len(retrieved) > request.registry.settings
                      ['controllers.users.list_length']),
        'list': result_list
    }
    raise HTTPOk(body=result)


@view_config(route_name='curuser')
def current_user(context, request):
    if request.logged_in:
        user = {
            'nickname': request.user['nickname']
        }
        raise HTTPOk(body=user)
    else:
        raise HTTPOk(body={})
