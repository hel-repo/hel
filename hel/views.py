import copy
import datetime
import hashlib
import json
import logging
import os

from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPFound,
    HTTPNotFound
)
from pyramid.request import Request
from pyramid.response import Response
from pyramid.security import forget, remember
from pyramid.view import view_config
import semantic_version as semver
from webob.headers import ResponseHeaders

from hel.resources import Package, Packages, User, Users
from hel.utils import jexc
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


# Home
@view_config(route_name='home', renderer='templates/home.pt')
def home(request):
    message = ''
    nickname = ''
    email = ''
    if request.authenticated_userid:
        nickname = request.authenticated_userid
    if any(x in ['log-out', 'log-in', 'register'] for x in request.POST):
        data = {}
        for k, v in request.POST.items():
            if k not in ['log-out', 'log-in', 'register']:
                data[k] = v
            else:
                data['action'] = k
        subrequest = Request.blank(
            '/auth', method='POST', POST=json.dumps(data),
            content_type='application/json')
        if hasattr(request, 'logged_in'):
            subrequest.logged_in = request.logged_in
        response = request.invoke_subrequest(subrequest, use_tweens=True)
        request.response.headers = response.headers
        cookie_headers = ResponseHeaders()
        for k, v in response.headers.items():
            if k.lower() == 'set-cookie':
                cookie_headers.add('Set-Cookie', v)
        message = response.json['message']
        if not nickname and 'nickname' in request.POST:
            nickname = request.POST['nickname'].strip()
        if 'email' in request.POST:
            email = request.POST['email'].strip()

        if (response.json['success'] and
                any(x in ['log-out', 'log-in'] for x in request.POST)):
            return HTTPFound(location=request.url, headers=cookie_headers)
    request.response.content_type = 'text/html'
    return {
        'project': 'hel',
        'message': message,
        'nickname': nickname,
        'email': email,
        'logged_in': request.logged_in,
        'version': request.version
    }


# Auth controller
@view_config(route_name='auth', renderer='json')
def auth(request):
    message = ''
    nickname = ''
    password = ''
    email = ''
    request.response.content_type = 'application/json'
    try:
        params = request.json_body
    except:
        message = Messages.bad_request
        jexc(HTTPBadRequest, message)
    if 'action' not in params:
        message = Messages.bad_request
    elif request.logged_in:
        nickname = request.authenticated_userid
        if params['action'] == 'log-out':
            headers = forget(request)
            request.response.status = '200 OK'
            for v in headers:
                request.response.headers.add(v[0], v[1])
            return {'success': True, 'message': Messages.logged_out}
    elif params['action'] == 'log-in':
        try:
            nickname = params['nickname'].strip()
            password = params['password'].strip()
        except KeyError:
            message = Messages.bad_request
        else:
            if nickname == '':
                message = Messages.empty_nickname
            elif password == '':
                message = Messages.empty_password
            else:
                pass_hash = hashlib.sha512(password.encode()).hexdigest()
                user = request.db['users'].find_one({'nickname': nickname})
                if user:
                    correct_hash = user['password']
                    if pass_hash == correct_hash:
                        headers = remember(request, nickname)
                        request.response.status = '200 OK'
                        for v in headers:
                            request.response.headers.add(v[0], v[1])
                        return {'message': Messages.logged_in,
                                'code': 200,
                                'title': 'OK',
                                'success': True}
                    else:
                        message = Messages.failed_login
                else:
                    message = Messages.failed_login
    elif params['action'] == 'register':
        try:
            nickname = params['nickname'].strip()
            email = params['email'].strip()
            password = params['password'].strip()
        except (KeyError, AttributeError):
            message = Messages.bad_request
        else:
            if nickname == '':
                message = Messages.empty_nickname
            elif email == '':
                message = Messages.empty_email
            elif password == '':
                message = Messages.empty_password
            else:
                pass_hash = hashlib.sha512(password.encode()).hexdigest()
                user = request.db['users'].find_one({'nickname': nickname})
                if user:
                    message = Messages.nickname_in_use
                else:
                    user = request.db['users'].find_one({'email': email})
                    if user:
                        message = Messages.email_in_use
                    else:
                        act_phrase = ''.join(
                            '{:02x}'.format(x) for x in os.urandom(
                                request.registry.settings
                                ['activation.length']))
                        act_till = (datetime.datetime.now() +
                                    datetime.timedelta(
                                        seconds=request.registry.settings
                                        ['activation.time']))
                        subrequest = Request.blank(
                            '/users', method='POST', POST=(
                                str(ModelUser(nickname=nickname,
                                              email=email,
                                              password=pass_hash,
                                              activation_phrase=act_phrase,
                                              activation_till=act_till))),
                            content_type='application/json')
                        subrequest.no_permission_check = True
                        response = request.invoke_subrequest(
                            subrequest, use_tweens=True)
                        if response.status_code == 201:
                            # TODO: send activation email
                            request.response.status = '200 OK'
                            return {'message':
                                    Messages.account_created_success,
                                    'code': 200,
                                    'title': 'OK',
                                    'success': True}
                        else:  # pragma: no cover
                            message = Messages.internal_error
                            log.error(
                                'Could not create a user: subrequest'
                                ' returned with status code %s!\n'
                                'Local variables in frame:%s',
                                response.status_code,
                                ''.join(['\n * ' + str(x) + ' = ' + str(y)
                                         for x, y in locals().items()])
                            )
    jexc(HTTPBadRequest, message)


# Someone requested this
# Mmm, okay
@view_config(route_name='teapot', renderer='json')
def teapot(request):
    return Response(
        status="418 I'm a teapot",
        content_type='application/json')


# Package controller
@view_config(request_method='PATCH',
             context=Package,
             renderer='json',
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
                jexc(HTTPConflict, Messages.pkg_name_conflict)
            if not Constants.name_pattern.match(v):
                jexc(HTTPBadRequest, Messages.pkg_bad_name)
        elif k in ['description', 'owner', 'license']:
            query[k] = check(
                v, str,
                Messages.type_mismatch % (k, 'str',))
        elif k == 'short_description':
            query[k] = check(
                v, str,
                Messages.type_mismatch % (k, 'str',))[:120]
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
                    jexc(HTTPBadRequest, str(e))
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
                            jexc(HTTPBadRequest, Messages.partial_ver)
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
                                    jexc(HTTPBadRequest, Messages.partial_ver)
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
                                    jexc(HTTPBadRequest, Messages.partial_ver)
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
                                            jexc(HTTPBadRequest, str(e))
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
                                            jexc(HTTPBadRequest,
                                                 Messages.wrong_dep_type)
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

    return Response(
        status='204 No Content',
        content_type='application/json')


@view_config(request_method='GET',
             context=Package,
             renderer='json',
             permission='pkg_view')
def get_package(context, request):
    r = context.retrieve()

    if r is None:
        jexc(HTTPNotFound)
    else:
        context.update({
            '$inc': {
                'stats.views': 1
            }
        })
        del r['_id']
        request.response.content_type = 'application/json'
        return replace_chars_in_keys(r, Constants.key_replace_char, '.')


@view_config(request_method='DELETE',
             context=Package,
             renderer='json',
             permission='pkg_delete')
def delete_package(context, request):
    context.delete()

    return Response(
        status='204 No Content')


@view_config(request_method='POST',
             context=Packages,
             renderer='json',
             permission='pkg_create')
def create_package(context, request):
    try:
        pkg = ModelPackage(True, **request.json_body)
    except (AttributeError, KeyError, TypeError, ValueError) as e:
        jexc(HTTPBadRequest, Messages.bad_package % str(e))
    except HTTPBadRequest:
        raise
    except Exception as e:  # pragma: no cover
        log.warn('Exception caught in create_package: %r.', e)
        jexc(HTTPBadRequest, Messages.bad_package % "'unknown'")
    if len([x for x in (request.db['packages']
                        .find({'name': pkg.data['name']}))]) > 0:
        jexc(HTTPConflict, Messages.pkg_name_conflict)
    if not Constants.name_pattern.match(pkg.data['name']):
        jexc(HTTPBadRequest, Messages.pkg_bad_name)
    data = pkg.pkg
    data['owner'] = request.authenticated_userid
    context.create(data)

    return Response(
        status='201 Created',
        content_type='application/json')


@view_config(request_method='GET',
             context=Packages,
             renderer='json',
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
    request.response.content_type = 'application/json'
    result = found[offset:offset+length]
    for v in result:
        if '_id' in v:
            del v['_id']

    return result


# User controller
@view_config(request_method='PATCH',
             context=User,
             renderer='json',
             permission='user_update')
def update_user(context, request):
    context.update(request.json_body, True)

    return Response(
        status='204 No Content',
        content_type='application/json')


@view_config(request_method='GET',
             context=User,
             renderer='json',
             permission='user_get')
def get_user(context, request):
    r = context.retrieve()

    if r is None:
        jexc(HTTPNotFound)
    else:
        data = {
            'nickname': r['nickname'],
            'groups': r['groups']
        }
        request.response.content_type = 'application/json'
        return data


@view_config(request_method='DELETE',
             context=User,
             renderer='json',
             permission='user_delete')
def delete_user(context, request):
    context.delete()

    return Response(
        status='204 No Content',
        content_type='application/json')


@view_config(request_method='POST',
             context=Users,
             renderer='json',
             permission='user_create')
def create_user(context, request):
    try:
        user = ModelUser(True, **request.json_body)
    except:
        jexc(HTTPBadRequest, Messages.bad_user)
    context.create(user.data)

    return Response(
        status='201 Created',
        content_type='application/json')


@view_config(request_method='GET',
             context=Users,
             renderer='json',
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
    request.response.content_type = 'application/json'
    res = retrieved[offset:offset+length]
    result = []
    for v in res:
        result.append({
                'nickname': v['nickname'],
                'groups': v['groups']
            })
    return result
