from pyramid.traversal import find_root
from bson.objectid import ObjectId


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
        return self.resource_name(ref=str(object_id), parent=self)


class MongoDocument(Resource):
    spec = {}

    def __init__(self, ref, parent):
        Resource.__init__(self, ref, parent)

        self.collection = parent.collection
        self.ref = ref

    def get_spec(self):
        return self.spec or {'_id': ObjectId(self.ref)}

    def retrieve(self):
        return self.collection.find_one(self.spec)

    def update(self, *args, **kwargs):
        self.collection.update(self.spec, args[0])

    def delete(self):
        self.collection.remove(self.spec)


class Package(MongoDocument):
    def __init__(self, ref, parent):
        MongoDocument.__init__(self, ref, parent)
        self.spec = {'name': ref}


class Packages(MongoCollection):
    collection_name = 'packages'
    resource_name = Package

    def __getitem__(self, ref):
        return Package(ref, self)


class User(MongoDocument):
    def __init__(self, ref, parent):
        MongoDocument.__init__(self, ref, parent)
        self.spec = {'nickname': ref}


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
