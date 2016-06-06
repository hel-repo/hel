import json
import logging
import os

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pymongo import MongoClient
from bson import json_util

from hel.resources import Root
from hel.utils.authentication import (
    HELAuthenticationPolicy,
    get_user,
    is_logged_in
)


log = logging.getLogger(__name__)


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

    # Auth
    auth_secret = "巏⇟ू攛劈ᜤ漢࿅䓽奧䬙摀曇䰤䙙൪ᴹ喼唣壆"
    if 'AUTH_SECRET' in os.environ:
        auth_secret = os.environ["AUTH_KEY"]
    authentication_policy = HELAuthenticationPolicy(
            auth_secret, hashalg='sha512')
    authorization_policy = ACLAuthorizationPolicy()

    # Custom config settings
    settings['activation.length'] = int(settings.get(
        'activation.length', '64'))
    settings['activation.time'] = int(settings.get(
        'activation.time', '3600'))
    settings['controllers.packages.list_length'] = int(settings.get(
        'controllers.packages.list_length', '20'))
    settings['controllers.users.list_length'] = int(settings.get(
        'controllers.users.list_length', '20'))

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
    elif 'mongo_db_url' in settings:
        url = settings['mongo_db_url']
    config.registry.mongo = MongoClient(url)

    def add_db(request):
        return config.registry.mongo.hel
    config.add_request_method(add_db, 'db', reify=True)

    # Auth again
    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(is_logged_in, 'logged_in', reify=True)

    # Setup routes
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.scan()
    return config.make_wsgi_app()
