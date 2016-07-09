import json

import semantic_version as semver

from hel.utils.constants import Constants
from hel.utils.messages import Messages
from hel.utils.query import replace_chars_in_keys


class ModelPackage:

    def __init__(self, strict=False, **kwargs):
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

        if strict:
            for k in ['name', 'description', 'short_description', 'authors',
                      'license', 'tags', 'versions', 'screenshots']:
                if k not in kwargs:
                    raise KeyError(k)

        for k, v in kwargs.items():
            if k in ['name', 'description', 'owner', 'license']:
                self.data[k] = str(v)
            elif k in ['authors', 'tags']:
                self.data[k] = [str(x) for x in v]
            elif k == 'versions':
                data = {}
                for ver, value in v.items():
                    files = {}
                    for file_url, f in value['files'].items():
                        files[str(file_url)] = {
                            'dir': str(f['dir']),
                            'name': str(f['name'])
                        }
                    dependencies = {}
                    for dep_name, dep_info in value['depends'].items():
                        if dep_info['type'] not in [
                                    'recommended',
                                    'optional',
                                    'required'
                                ]:
                            raise ValueError(Messages.wrong_dep_type)
                        semver.Spec(dep_info['version'])
                        dependencies[str(dep_name)] = {
                            'version': str(dep_info['version']),
                            'type': str(dep_info['type'])
                        }
                    data[str(semver.Version.coerce(str(ver)))] = {
                        'files': files,
                        'depends': dependencies
                    }
                self.data[k] = data
            elif k == 'screenshots':
                self.data[k] = {str(url): str(desc)
                                for url, desc in v.items()}
            elif k == 'short_description':
                self.data[k] = str(v)[:140]

    @property
    def json(self):
        return json.dumps(self.pkg)

    @property
    def pkg(self):
        return replace_chars_in_keys(
            self.data, '.', Constants.key_replace_char)

    def __str__(self):
        return json.dumps(self.data)


class ModelUser:

    def __init__(self, strict=False, **kwargs):
        self.data = {
            'nickname': '',
            'groups': [],
            'password': '',
            'email': '',
            'activation_phrase': '',
            'activation_till': ''
        }

        if strict:
            for v in ['nickname', 'password', 'email', 'activation_phrase',
                      'activation_till']:
                if v not in kwargs:
                    raise KeyError(v)

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
