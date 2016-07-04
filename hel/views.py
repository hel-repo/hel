import datetime
import hashlib
import logging
import os

from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from pyramid.request import Request
from pyramid.response import Response
from pyramid.security import remember, forget
from pyramid.view import view_config

from hel.resources import Package, Packages, User, Users
from hel.utils.constants import Constants
from hel.utils.messages import Messages
from hel.utils.models import ModelUser
from hel.utils.query import (
    PackagesSearcher,
    check,
    check_list_of_strs,
    replace_chars_in_keys
)


log = logging.getLogger(__name__)


# Home page
@view_config(route_name='home', renderer='templates/home.pt')
def home(request):
    message = ''
    nickname = ''
    password = ''
    email = ''
    passwd_confirm = ''
    if not hasattr(request, 'logged_in'):
        request.logged_in = False
    if request.logged_in:
        nickname = request.authenticated_userid
        if 'log-out' in request.POST:
            headers = forget(request)
            return HTTPFound(location=request.url, headers=headers)
    elif 'log-in' in request.POST:
        try:
            nickname = request.POST['nickname'].strip()
            password = request.POST['password'].strip()
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
                        response = HTTPFound(location=request.url,
                                             headers=headers)
                        return response
                    else:
                        message = Messages.failed_login
                else:
                    message = Messages.failed_login
    elif 'register' in request.POST:
        try:
            nickname = request.POST['nickname'].strip()
            email = request.POST['email'].strip()
            password = request.POST['password'].strip()
            passwd_confirm = request.POST['passwd-confirm'].strip()
        except KeyError:
            message = Messages.bad_request
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
                    if password != passwd_confirm:
                        message = Messages.password_mismatch
                    else:
                        act_phrase = os.urandom(
                            request.registry.settings
                            ['activation.length']).hex()
                        act_till = (datetime.datetime.now() +
                                    datetime.timedelta(
                                        seconds=request.registry.settings
                                        ['activation.time']))
                        subrequest = Request.blank(
                            '/users', method='POST', POST=(
                                str(ModelUser(nickname=nickname, email=email,
                                              password=pass_hash,
                                              activation_phrase=act_phrase,
                                              activation_till=act_till))),
                            content_type='application/json')
                        subrequest.no_permission_check = True
                        response = request.invoke_subrequest(
                            subrequest, use_tweens=True)
                        if response.status_code == 201:
                            # TODO: send activation email
                            message = Messages.account_created_success
                        else:
                            message = Messages.internal_error
                            log.error(
                                'Could not create a user: subrequest'
                                ' returned with status code %s!\n'
                                'Local variables in frame:%s',
                                response.status_code,
                                ''.join(['\n * ' + str(x) + ' = ' + str(y)
                                         for x, y in locals().items()])
                            )
    return {
        'project': 'hel',
        'message': message,
        'nickname': nickname,
        'email': email,
        'logged_in': request.logged_in
    }


# Someone requested this
# Mmm, okay
@view_config(route_name='teapot', renderer='json')
def teapot(request):
    return Response(
        status="418 I'm a teapot",
        content_type='application/json; charset=UTF-8')


# Package controller
@view_config(request_method='PUT',
             context=Package,
             renderer='json',
             permission='pkg_update')
def update_package(context, request):
    query = {}
    for k, v in request.json_body.items():
        if k in ['name', 'description', 'owner', 'license']:
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
            for num, ver in v.items():
                check(
                    num, str,
                    Messages.type_mismatch % ('version', 'str',))
                if ver is None:
                    query[k] = query[k] or {}
                    query[k]['versions'] = query[k]['versions'] or {}
                    query[k]['versions'][num] = None
                else:
                    check(
                        ver, dict,
                        Messages.type_mismatch % ('version_info', 'dict',))
                    if 'files' in ver:
                        check(
                            ver['files'], dict,
                            Messages.type_mismatch % ('files', 'dict',))
                        for url, file_info in ver['files'].items():
                            if file_info is None:
                                query[k] = query[k] or {}
                                query[k]['versions'] = (
                                    query[k]['versions'] or {})
                                query[k]['versions'][num] = (
                                    query[k]['versions'][num] or {})
                                query[k]['versions'][num]['files'][url] = None
                            else:
                                check(
                                    file_info, dict,
                                    Messages.type_mismatch % (
                                        'file_info', 'dict',))
                                check(
                                    url, str,
                                    Messages.type_mismatch % ('url', 'str',))
                                query[k] = query[k] or {}
                                query[k]['versions'] = (
                                    query[k]['versions'] or {})
                                query[k]['versions'][num] = (
                                    query[k]['versions'][num] or {})
                                if ('dir' in file_info and
                                        check(
                                            file_info['dir'], str,
                                            Messages.type_mismatch % (
                                                'file_dir', 'str',)) or
                                        'name' in file_info and
                                        check(
                                            file_info['name'], str,
                                            Messages.type_mismatch % (
                                                k, 'str',))):
                                    (query[k]['versions'][num]['files']
                                     [url]) = {}
                                if 'dir' in file_info:
                                    (query[k]['versions'][num]['files']
                                     [url]['dir']) = file_info['dir']
                                if 'name' in file_info:
                                    (query[k]['versions'][num]['files']
                                     [url]['dir']) = file_info['name']

                    if 'depends' in ver:
                        check(
                            ver['depends'], dict,
                            Messages.type_mismatch % ('depends', 'dict',))
                        for dep_name, dep_info in ver['depends'].items():
                            if dep_info is None:
                                query[k] = query[k] or {}
                                query[k]['versions'] = (
                                    query[k]['versions'] or {})
                                query[k]['versions'][num] = (
                                    query[k]['versions'][num] or {})
                                if ('version' in dep_info and
                                        check(
                                            dep_info['version'], str,
                                            Messages.type_mismatch % (
                                                'dep_version', 'str',)) or
                                        'type' in dep_info and
                                        check(
                                            dep_info['type'], str,
                                            Messages.type_mismatch % (
                                                'dep_type', 'str',))):
                                    query[k]['versions'][num]['depends'] = {}
                                if 'version' in dep_info:
                                    (query[k]['versions'][num]['depends']
                                     [dep_name]['version']) = (
                                        dep_info['version'])
                                if 'type' in dep_info:
                                    (query[k]['versions'][num]['depends']
                                     [dep_name]['type']) = dep_info['type']
        elif k == 'screenshots':
            check(v, dict, Messages.type_mismatch % (k, 'dict',))
            for url, desc in v:
                check(
                    url, str,
                    Messages.type_mismatch % ('screenshot_key', 'str',))
                if desc is None or check(
                        desc, str,
                        Messages.type_mismatch % ('screenshot_desc', 'str',)):
                    query[k][url] = desc
    query = replace_chars_in_keys(query, '.', Constants.key_replace_char)
    context.update(query, True)

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET',
             context=Package,
             renderer='json',
             permission='pkg_view')
def get_package(context, request):
    r = context.retrieve()

    if r is None:
        raise HTTPNotFound()
    else:
        return r


@view_config(request_method='DELETE',
             context=Package,
             renderer='json',
             permission='pkg_delete')
def delete_package(context, request):
    context.delete()

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='POST',
             context=Packages,
             renderer='json',
             permission='pkg_create')
def create_package(context, request):
    data = replace_chars_in_keys(request.json_body, '.',
                                 Constants.key_replace_char)
    context.create(data)

    return Response(
        status='201 Created',
        content_type='application/json; charset=UTF-8')


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
    return found[offset:offset+length]


# User controller
@view_config(request_method='PUT',
             context=User,
             renderer='json',
             permission='user_update')
def update_user(context, request):
    context.update(request.json_body, True)

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET',
             context=User,
             renderer='json',
             permission='user_get')
def get_user(context, request):
    r = context.retrieve()

    if r is None:
        raise HTTPNotFound()
    else:
        return r


@view_config(request_method='DELETE',
             context=User,
             renderer='json',
             permission='user_delete')
def delete_user(context, request):
    context.delete()

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='POST',
             context=Users,
             renderer='json',
             permission='user_create')
def create_user(context, request):
    context.create(request.json_body)

    return Response(
        status='201 Created',
        content_type='application/json; charset=UTF-8')


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
    retrieved = context.retrieve(params)
    return retrieved[offset:offset+length]
