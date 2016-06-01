from hel.resources import Package, Packages, User, Users
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.response import Response


# Home page
@view_config(route_name='home', renderer='templates/home.pt')
def home(request):
    return {'project': 'hel'}


# Package controller
@view_config(request_method='PUT', context=Package, renderer='json')
def update_package(context, request):
    r = context.update(request.json_body, True)

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET', context=Package, renderer='json')
def get_package(context, request):
    r = context.retrieve()

    if r is None:
        raise HTTPNotFound()
    else:
        return r


@view_config(request_method='DELETE', context=Package, renderer='json')
def delete_package(context, request):
    context.delete()

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='POST', context=Packages, renderer='json')
def create_package(context, request):
    r = context.create(request.json_body)

    return Response(
        status='201 Created',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET', context=Packages, renderer='json')
def list_packages(context, request):
    return context.retrieve(request.GET)


# User controller
@view_config(request_method='PUT', context=User, renderer='json')
def update_user(context, request):
    r = context.update(request.json_body, True)

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET', context=User, renderer='json')
def get_user(context, request):
    r = context.retrieve()

    if r is None:
        raise HTTPNotFound()
    else:
        return r


@view_config(request_method='DELETE', context=User, renderer='json')
def delete_user(context, request):
    context.delete()

    return Response(
        status='202 Accepted',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='POST', context=Users, renderer='json')
def create_user(context, request):
    r = context.create(request.json_body)

    return Response(
        status='201 Created',
        content_type='application/json; charset=UTF-8')


@view_config(request_method='GET', context=Users, renderer='json')
def list_users(context, request):
    return context.retrieve(request.GET)
