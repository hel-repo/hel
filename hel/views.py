import datetime
import hashlib
import logging
import os

from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPForbidden
from pyramid.request import Request
from pyramid.response import Response
from pyramid.security import remember, forget, Allowed
from pyramid.view import view_config

from hel.resources import Package, Packages, User, Users
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
    if request.logged_in:
        nickname = request.authenticated_userid
        if 'log-out' in request.params:
            headers = forget(request)
            return HTTPFound(location=request.url, headers=headers)
    elif 'log-in' in request.params:
        try:
            nickname = request.params['nickname']
            password = request.params['password']
            pass_hash = hashlib.sha512(password.encode()).hexdigest()
            user = request.db['users'].find_one({'nickname': nickname})
            if user:
                correct_hash = user['password']
                if pass_hash == correct_hash:
                    headers = remember(request, nickname)
                    return HTTPFound(location=request.url, headers=headers)
                else:
                    message = 'Incorrect nickname and/or password.'
            else:
                message = 'Incorrect nickname and/or password.'
        except KeyError:
            message = 'Bad request.'
    elif 'register' in request.params:
        try:
            nickname = request.params['nickname']
            email = request.params['email']
            password = request.params['password']
            passwd_confirm = request.params['passwd-confirm']
        except KeyError:
            message = 'Bad request.'
        pass_hash = hashlib.sha512(password.encode()).hexdigest()
        user = request.db['users'].find_one({'nickname': nickname})
        if user:
            message = 'This nickname is already in use.'
        else:
            user = request.db['users'].find_one({'email': email})
            if user:
                message = 'This email address is already in use.'
            else:
                if password != passwd_confirm:
                    message = 'Passwords do not match.'
                else:
                    # Praise the python's 80-chars-long line limit!
                    # The code now looks ugly :(
                    act_phrase = os.urandom(
                        request.registry.settings \
                            ['activation.length']).hex()
                    act_till = (datetime.datetime.now()
                              + datetime.timedelta(
                                seconds=request.registry.settings \
                                    ['activation.time']))
                    subrequest = Request.blank('/users', method='POST',
                                               POST='{' + """
                        "nickname": "{nickname}",
                        "email": "{email}",
                        "password": "{password}",
                        "groups": [],
                        "activation_phrase": "{act_phrase}",
                        "activation_till": "{act_till}"
                    """.format(nickname=nickname, email=email,
                               password=pass_hash, act_phrase=act_phrase,
                               act_till=act_till) + '}')
                    subrequest.no_permission_check = True
                    response = request.invoke_subrequest(
                        subrequest, use_tweens=True)
                    if response.status_code == 201:
                        # TODO: send activation email
                        message = 'Account created successfully!'
                    else:
                        message = 'Internal error.'
                        log.error('Could not create a user: subrequest'
                            ' returned with status code %s!\n'
                            'Local variables in frame:%s',
                            response.status_code,
                            ''.join(['\n * ' + str(x) + ' = ' + str(y) \
                                for x, y in locals().items()]))
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
    r = context.update(request.json_body, True)

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
    r = context.create(request.json_body)

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
    r = context.update(request.json_body, True)

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
    r = context.create(request.json_body)

    return Response(
        status='201 Created',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET',
             context=Users,
             renderer='json',
             permission='user_list')
def list_users(context, request):
    return context.retrieve(request.GET)
