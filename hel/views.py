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
from hel.utils.messages import Messages
from htl.utils.models import ModelUser
from hel.utils.query import PackagesSearchQuery


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
        if 'log-out' in request.params:
            headers = forget(request)
            return HTTPFound(location=request.url, headers=headers)
    elif 'log-in' in request.params:
        try:
            nickname = request.params['nickname'].strip()
            password = request.params['password'].strip()
        except KeyError:
            message = Messages.bad_request
        else:
            log.debug(
                'Log in, local variables:%s',
                ''.join(['\n * ' + str(x) + ' = ' + str(y)
                         for x, y in locals().items()])
            )
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
                        return HTTPFound(location=request.url, headers=headers)
                    else:
                        message = Messages.failed_login
                else:
                    message = Messages.failed_login
    elif 'register' in request.params:
        try:
            nickname = request.params['nickname'].strip()
            email = request.params['email'].strip()
            password = request.params['password'].strip()
            passwd_confirm = request.params['passwd-confirm'].strip()
        except KeyError:
            message = Messages.bad_request
        log.debug(
            'Register, local variables:%s',
            ''.join(['\n * ' + str(x) + ' = ' + str(y)
                     for x, y in locals().items()])
        )
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
                                              activation_till=act_till))))
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


# Package controller
@view_config(request_method='PUT',
             context=Package,
             renderer='json',
             permission='pkg_update')
def update_package(context, request):
    context.update(request.json_body, True)

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
    context.create(request.json_body)

    return Response(
        status='201 Created',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET',
             context=Packages,
             renderer='json',
             permission='pkgs_view')
def list_packages(context, request):
    search_query = PackagesSearchQuery(request.GET.dict_of_lists())
    query = search_query()
    return context.retrieve(query)


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
    return context.retrieve(request.GET)
