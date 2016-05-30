from hel.resources import Package, Packages
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from pyramid.response import Response


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def home(request):
    return {'project': 'hel'}


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
    return context.retrieve()

