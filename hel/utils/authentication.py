from pyramid.authentication import AuthTktAuthenticationPolicy as Policy
from pyramid.security import Everyone, Authenticated

from hel.resources import Users

class HELAuthenticationPolicy(Policy):

    def authenticated_userid(self, request):
        userid = self.unauthenticated_userid(request)
        if userid:
            try:
                Users[userid]
            except KeyError:
                pass
            else:
                return userid

    def effective_principals(self, request):
        principals = [Everyone]
        userid = self.authenticated_userid(request)
        if userid:
            principals += [Authenticated]
            user = Users[userid].retrieve()
            principals += ['~' + x for x in user['groups']]
        return principals
