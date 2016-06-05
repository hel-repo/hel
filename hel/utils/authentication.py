from pyramid.authentication import AuthTktAuthenticationPolicy as Policy
from pyramid.security import Everyone, Authenticated

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
        except AttributeError:
            pass
        if user:
            principals += [Authenticated, '@' + user['nickname']]
            principals += ['~' + x for x in user['groups']]
            if not 'act_till' in user and not 'act_phrase' in user:
                principals += ['activated']
        elif hasattr(request, 'no_permission_check') \
                and request.no_permission_check:
            principals += ['~allperms']
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
