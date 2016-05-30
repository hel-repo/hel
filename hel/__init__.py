import os

from hel.resources import Root
from pyramid.config import Configurator
from pymongo import MongoClient

from bson import json_util
import json


class MongoJSONRenderer:
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        request = system.get('request')
        if request is not None:
            if not hasattr(request, 'response_content_type'):
                request.response_content_type = 'application/json'
        return json.dumps(value, default=json_util.default)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=Root)
    config.include('pyramid_chameleon')
    config.add_renderer('json', MongoJSONRenderer)
    config.add_static_view('static', 'static', cache_max_age=3600)

    # Setup MondoDB
    if 'MONGODB_URL' in os.environ:
        url = os.environ['MONGODB_URL']
    else:
        url = 'mongodb://localhost:27017/'
    config.registry.mongo = MongoClient(url)

    def add_db(request):
        return config.registry.mongo.hel
    config.add_request_method(add_db, 'db', reify=True)

    # Setup routes
    config.add_route('home', '/')
    config.scan()
    return config.make_wsgi_app()
