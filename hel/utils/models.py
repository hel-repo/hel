import json


class ModelPackage:

    def __init__(self, **kwargs):
        self.data = {
            'name': '',
            'description': '',
            'short_description': '',
            'owner': '',
            'authors': [],
            'license': '',
            'tags': [],
            'versions': {},
            'screenshots': {}
        }

        for k, v in kwargs.items():
            if k in ['name', 'description', 'owner', 'license']:
                self.data[k] = str(v)
            elif k in ['authors', 'tags']:
                self.data[k] = [str(x) for x in v]
            elif k == 'versions':
                for ver, value in v.items():
                    files = {}
                    for file_url, f in value['files']:
                        files[str(file_url)] = {
                            'dir': str(f['dir']),
                            'name': str(f['name'])
                        }
                    dependencies = {}
                    for dep_name, dep_info in value['depends']:
                        dependencies[str(dep_name)] = {
                            'version': str(dep_info['version']),
                            'type': str(dep_info['type'])
                        }
                    v[str(ver)] = {
                        'files': files,
                        'depends': dependencies
                    }
                self.data[k] = v
            elif k == 'screenshots':
                self.data[k] = {str(url): str(desc)
                                for url, desc in v.items()}
            elif k == 'short_description':
                self.data[k] = str(v)[:140]

    def json(self):
        return json.dumps(self.data)

    def __str__(self):
        return self.json()


class ModelUser:

    def __init__(self, **kwargs):
        self.data = {
            'nickname': '',
            'groups': [],
            'password': '',
            'email': '',
            'activation_phrase': '',
            'activation_till': ''
        }

        for k, v in kwargs.items():
            if k in ['nickname', 'activation_till', 'password',
                     'email', 'activation_phrase']:
                self.data[k] = str(v)
            elif k == 'groups':
                self.data[k] = [str(x) for x in v]

    def json(self):
        return json.dumps(self.data)

    def __str__(self):
        return self.json()
