import os
import json

from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy
from pymongo import MongoClient
from bson import json_util

from hel.resources import Root
from hel.utils.authentication import HELAuthenticationPolicy


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

    auth_secret = "巏⇟ू攛劈ᜤ漢࿅䓽奧䬙摀曇䰤䙙൪ᴹ喼唣壆"
    if 'AUTH_SECRET' in os.environ:
        auth_secret = os.environ["AUTH_KEY"]
    authentication_policy = HELAuthenticationPolicy(
            auth_secret, hashalg='sha512')
    authorization_policy = ACLAuthorizationPolicy()

    config = Configurator(settings=settings, root_factory=Root)
    config.set_authentication_policy(authentication_policy)
    config.set_authorization_policy(authorization_policy)
    config.include('pyramid_chameleon')
    config.add_renderer('json', MongoJSONRenderer)
    config.add_static_view('static', 'static', cache_max_age=3600)

    # Setup MongoDB
    url = 'mongodb://localhost:27017/'
    if 'MONGODB_URL' in os.environ:
        url = os.environ['MONGODB_URL']
    config.registry.mongo = MongoClient(url)

    def add_db(request):
        return config.registry.mongo.hel
    config.add_request_method(add_db, 'db', reify=True)

    # Setup routes
    config.add_route('home', '/')
    config.scan()
    return config.make_wsgi_app()
