from bson.objectid import ObjectId
from pyramid.security import (
    Allow,
    Deny,
    Everyone,
    Authenticated,
    ALL_PERMISSIONS
)
from pyramid.traversal import find_root


class Resource(dict):

    def __init__(self, ref, parent, **kwargs):
        super().__init__(**kwargs)
        self.__name__ = ref
        self.__parent__ = parent

    def __repr__(self):
        # use standard object representation (not dict's)
        return object.__repr__(self)

    def add_child(self, ref, klass):
        resource = klass(ref=ref, parent=self)
        self[ref] = resource

    @classmethod
    def __acl__(cls):
        return [
            (Allow, '~admins', ALL_PERMISSIONS,),
            (Allow, '~system', ALL_PERMISSIONS,),
            (Allow, Everyone, 'pkg_view',),
            (Allow, Everyone, 'pkgs_view',),
            (Deny, '~banned', 'pkg_create',),
            (Allow, Authenticated, 'pkg_create',),  # TODO: Activated only
            (Allow, Everyone, 'user_list',),
            (Deny, '~banned', ALL_PERMISSIONS,)
        ]


class MongoCollection(Resource):

    collection_name = ""
    resource_name = Resource

    @property
    def collection(self):
        root = find_root(self)
        request = root.request
        return request.db[self.collection_name]

    def retrieve(self, query=None):
        return [elem for elem in self.collection.find(query)]

    def create(self, document):
        object_id = self.collection.insert(document)
        return self.resource_name(ref=str(object_id), parent=self,
                                  id_as_ref=True)


class MongoDocument(Resource):

    spec = None

    def __init__(self, ref, parent):
        Resource.__init__(self, ref, parent)

        self.collection = parent.collection
        self.ref = ref

    def get_spec(self):
        return self.spec or {'_id': ObjectId(self.ref)}

    def retrieve(self):
        return self.collection.find_one(self.get_spec())

    def update(self, *args, **kwargs):
        self.collection.find_and_modify(self.get_spec(), args[0])

    def delete(self):
        self.collection.remove(self.get_spec())


class Package(MongoDocument):

    owners = None

    def __init__(self, ref, parent, id_as_ref=False):
        MongoDocument.__init__(self, ref, parent)
        if id_as_ref:
            self.get_owners()
        self.spec = {'name': ref}
        if not id_as_ref:
            self.get_owners()

    def get_owners(self):
        try:
            self.owners = self.owners or self.retrieve()['owners']
        except:
            pass
        return self.owners

    def __acl__(self):
        data = super().__acl__()
        if self.owners:
            for owner in self.owners:
                data += [(Allow, '@' + owner, ('pkg_delete', 'pkg_update',),)]
        return data


class Packages(MongoCollection):

    collection_name = 'packages'
    resource_name = Package

    def __getitem__(self, ref):
        return Package(ref, self)


class User(MongoDocument):

    def __init__(self, ref, parent, id_as_ref=False):
        MongoDocument.__init__(self, ref, parent)
        self.spec = {'nickname': ref}

    def __acl__(self):
        return super().__acl__() + [
            (Allow, '@' + self.spec['nickname'], ('user_get', 'user_update'),),
        ]


class Users(MongoCollection):

    collection_name = 'users'
    resource_name = User

    def __getitem__(self, ref):
        return User(ref, self)


class Root(Resource):

    def __init__(self, request):
        Resource.__init__(self, ref='', parent=None)

        self.request = request
        self.add_child('packages', Packages)
        self.add_child('users', Users)
