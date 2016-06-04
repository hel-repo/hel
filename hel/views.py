import hashlib

from pyramid.httpexceptions import HTTPNotFound, HTTPFound, HTTPForbidden
from pyramid.response import Response
from pyramid.security import remember, forget
from pyramid.view import view_config

from hel.resources import Package, Packages, User, Users
from hel.utils.query import PackagesSearchQuery


# Home page
@view_config(route_name='home', renderer='templates/home.pt')
def home(request):
    message = ''
    nickname = ''
    password = ''
    email = ''
    passwd_confirm = ''
    if 'log-in' in request.params:
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
        except KeyError:
            message = 'Bad request.'
    elif 'register' in request.params:
        pass
    return {
        'project': 'hel',
        'message': message,
        'nickname': nickname,
        'password': password,
        'passwd_confirm': passwd_confirm,
        'email': email,
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
