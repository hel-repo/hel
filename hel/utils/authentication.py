from pyramid.authentication import AuthTktAuthenticationPolicy as Policy
from pyramid.security import Everyone, Authenticated

class HELAuthenticationPolicy(Policy):

    def authenticated_userid(self, request):
        if request.user:
            return '@' + request.user['nickname']

    def effective_principals(self, request):
        principals = [Everyone]
        user = request.user
        if user:
            principals += [Authenticated, '@' + user['nickname']]
            principals += ['~' + x for x in user['groups']]
        return principals
