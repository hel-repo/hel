from bson.objectid import ObjectId
from pyramid.security import Allow, Everyone, Authenticated, ALL_PERMISSIONS
from pyramid.traversal import find_root


class Resource(dict):

    acl = []

    def __init__(self, ref, parent, **kwargs):
        super().__init__(**kwargs)
        self.__name__ = ref
        self.__parent__ = parent
        self.acl += [
            (Allow, '~admins', ALL_PERMISSIONS,),
            (Allow, '~system', ALL_PERMISSIONS,),
            (Allow, '~allperms', ALL_PERMISSIONS,)
        ]

    def __repr__(self):
        # use standard object representation (not dict's)
        return object.__repr__(self)

    def add_child(self, ref, klass):
        resource = klass(ref=ref, parent=self)
        self[ref] = resource

    def __acl__(self):
        return self.acl


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

    owner = None

    def __init__(self, ref, parent, id_as_ref=False):
        MongoDocument.__init__(self, ref, parent)
        if id_as_ref:
            self.get_owner()
        self.spec = {'name': ref}
        if not id_as_ref:
            self.get_owner()

    def get_owner(self):
        try:
            self.owner = self.owner or self.retrieve()['owner']
        except:
            pass
        return self.owner

    def __acl__(self):
        data = self.acl + [
            (Allow, Everyone, 'pkg_view',),
        ]
        if self.owner:
            data += [(Allow, self.owner, ('pkg_delete', 'pkg_update',),)]
        return data


class Packages(MongoCollection):

    collection_name = 'packages'
    resource_name = Package

    def __getitem__(self, ref):
        return Package(ref, self)

    def __acl__(self):
        return self.acl + [
            (Allow, Everyone, 'pkgs_view',),
            (Allow, Authenticated, 'pkg_create',)  # TODO: Activated only
        ]


class User(MongoDocument):

    def __init__(self, ref, parent, id_as_ref=False):
        MongoDocument.__init__(self, ref, parent)
        self.spec = {'nickname': ref}

    def __acl__(self):
        return self.acl + [
            (Allow, '@' + self.ref, ('user_update', 'user_get',),),
        ]


class Users(MongoCollection):

    collection_name = 'users'
    resource_name = User

    def __getitem__(self, ref):
        return User(ref, self)

    def __acl__(self):
        return self.acl + [
            (Allow, Everyone, 'user_list',)
        ]


class Root(Resource):

    def __init__(self, request):
        Resource.__init__(self, ref='', parent=None)

        self.request = request
        self.add_child('packages', Packages)
        self.add_child('users', Users)
