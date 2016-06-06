import json


class ModelPackage:

    data = {
        'name': '',
        'description': '',
        'short_description': '',
        'owner': '',
        'authors': [],
        'license': '',
        'tags': [],
        'versions': [],
        'screenshots': []
    }

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k in ['name', 'description', 'owner', 'license']:
                self.data[k] = str(v)
            elif k in ['authors', 'tags']:
                self.data[k] = [str(x) for x in v]
            elif k == 'versions':
                for num, ver in v.enumerate():
                    v[num] = {
                        'number': str(ver['number']),
                        'files': [{'url': str(x['url']),
                                   'dir': str(x['dir']),
                                   'name': str(x['name'])}
                                  for x in ver['files']],
                        'depends': [{'name': str(x['name']),
                                     'version': str(x['version']),
                                     'type': str(x['type'])}
                                    for x in ver['depends']]
                    }
                self.data[k] = v
            elif k == 'screenshots':
                self.data[k] = [{'url': str(x['url']),
                                 'description': str(x['description'])}
                                for x in v['screenshots']]
            elif k == 'short_description':
                self.data[k] = str(v)[:140]

    def json(self):
        return json.dumps(self.data)

    def __str__(self):
        return self.json()


class ModelUser:

    data = {
        'nickname': '',
        'groups': [],
        'password': '',
        'email': '',
        'activation_phrase': '',
        'activation_till': ''
    }

    def __init__(self, **kwargs):
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
