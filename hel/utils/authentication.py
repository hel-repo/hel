# -*- coding: utf-8 -*-
import hashlib

from pyramid.authentication import AuthTktAuthenticationPolicy as Policy
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import ACLAllowed, Everyone, Authenticated


class HELAuthenticationPolicy(Policy):

    def authenticated_userid(self, request):
        if request.user:
            if request.user['logged_in']:
                return '@' + request.user['nickname']

    def effective_principals(self, request):
        principals = [Everyone]
        user = None
        try:
            user = request.user
        except AttributeError:  # pragma: no cover
            pass
        if user:
            principals += [Authenticated, '@' + user['nickname']]
            principals += ['~' + x for x in user['groups']]
            if 'act_till' not in user and 'act_phrase' not in user:
                principals += ['activated']
        elif (hasattr(request, 'no_permission_check') and
                request.no_permission_check):
            principals += ['~system']
        return principals

    def remember(self, request, nickname):
        headers = Policy.remember(self, request, nickname)
        request.db['users'].find_and_modify(
            query={
                'nickname': nickname
            },
            update={
                '$set': {
                    'logged_in': True
                }
            }
        )
        return headers

    def forget(self, request):
        nickname = request.authenticated_userid
        headers = Policy.forget(self, request)
        request.db['users'].find_and_modify(
            query={
                'nickname': nickname
            },
            update={
                '$set': {
                    'logged_in': False
                }
            }
        )
        return headers


def get_user(request):
    userid = request.unauthenticated_userid
    if userid:
        return request.db['users'] \
            .find_one({'nickname': userid})


def is_logged_in(request):
    if Authenticated in request.effective_principals:
        return True
    return False


def has_permission(request, permission, context=None):
    if request.has_permission(permission, context):
        return True
    raise HTTPForbidden


def salt(request, password, username):
    hash_data = (username.encode() +
                 request.registry.settings['authentication.salt'] +
                 password.encode())
    return hashlib.sha512(hash_data).hexdigest()
