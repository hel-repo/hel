from hel.utils.models import ModelPackage


pkg1 = ModelPackage(
    name='package-1',
    description='My first test package.',
    short_description='1 package.',
    owner='Tester',
    authors=['Tester', 'Crackes'],
    license='mylicense-1',
    tags=['aaa', 'xxx', 'zzz'],
    versions={
        '1.1.1': {
            'files': {
                'http://example.com/file17': {
                    'dir': '/bin',
                    'name': 'test-1-file-7'
                },
                'http://example.com/file18': {
                    'dir': '/lib',
                    'name': 'test-1-file-8'
                },
                'http://example.com/file19': {
                    'dir': '/man',
                    'name': 'test-1-file-9'
                }
            },
            'depends': {
                'dpackage-1': {
                    'version': '~1.1',
                    'type': 'required'
                },
                'dpackage-2': {
                    'version': '^5',
                    'type': 'optional'
                },
                'dpackage-3': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 13.'
        },
        '1.1.0': {
            'files': {
                'http://example.com/file14': {
                    'dir': '/bin',
                    'name': 'test-1-file-4'
                },
                'http://example.com/file15': {
                    'dir': '/lib',
                    'name': 'test-1-file-5'
                },
                'http://example.com/file16': {
                    'dir': '/man',
                    'name': 'test-1-file-6'
                }
            },
            'depends': {
                'dpackage-1': {
                    'version': '~1.1',
                    'type': 'required'
                },
                'dpackage-2': {
                    'version': '^5',
                    'type': 'optional'
                },
                'dpackage-3': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 12.'
        },
        '1.0.0': {
            'files': {
                'http://example.com/file11': {
                    'dir': '/bin',
                    'name': 'test-1-file-1'
                },
                'http://example.com/file12': {
                    'dir': '/lib',
                    'name': 'test-1-file-2'
                },
                'http://example.com/file13': {
                    'dir': '/man',
                    'name': 'test-1-file-3'
                }
            },
            'depends': {
                'dpackage-1': {
                    'version': '~1.1',
                    'type': 'required'
                },
                'dpackage-2': {
                    'version': '^5',
                    'type': 'optional'
                },
                'dpackage-3': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 11.'
        }
    },
    screenshots={
        'http://img.example.com/img11': 'test-1-img-1',
        'http://img.example.com/img12': 'test-1-img-2',
        'http://img.example.com/img13': 'test-1-img-3'
    }
)

pkg2 = ModelPackage(
    name='package-2',
    description='My second test package.',
    short_description='2 package.',
    owner='Tester',
    authors=['Tester', 'Kjers'],
    license='mylicense-2',
    tags=['xxx', 'yyy', 'ccc'],
    versions={
        '1.0.2': {
            'files': {
                'http://example.com/file27': {
                    'dir': '/bin',
                    'name': 'test-2-file-7'
                },
                'http://example.com/file28': {
                    'dir': '/lib',
                    'name': 'test-2-file-8'
                },
                'http://example.com/file29': {
                    'dir': '/man',
                    'name': 'test-2-file-9'
                }
            },
            'depends': {
                'dpackage-4': {
                    'version': '~1',
                    'type': 'required'
                },
                'dpackage-5': {
                    'version': '^3.5.6',
                    'type': 'optional'
                },
                'dpackage-6': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 23.'
        },
        '1.0.1': {
            'files': {
                'http://example.com/file24': {
                    'dir': '/bin',
                    'name': 'test-2-file-4'
                },
                'http://example.com/file25': {
                    'dir': '/lib',
                    'name': 'test-2-file-5'
                },
                'http://example.com/file26': {
                    'dir': '/man',
                    'name': 'test-2-file-6'
                }
            },
            'depends': {
                'dpackage-4': {
                    'version': '~1',
                    'type': 'required'
                },
                'dpackage-5': {
                    'version': '^3.5.6',
                    'type': 'optional'
                },
                'dpackage-6': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 22.'
        },
        '1.0.0': {
            'files': {
                'http://example.com/file21': {
                    'dir': '/bin',
                    'name': 'test-2-file-1'
                },
                'http://example.com/file22': {
                    'dir': '/lib',
                    'name': 'test-2-file-2'
                },
                'http://example.com/file23': {
                    'dir': '/man',
                    'name': 'test-2-file-3'
                }
            },
            'depends': {
                'dpackage-4': {
                    'version': '~1',
                    'type': 'required'
                },
                'dpackage-5': {
                    'version': '^3.5.6',
                    'type': 'optional'
                },
                'dpackage-6': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 21.'
        }
    },
    screenshots={
        'http://img.example.com/img21': 'test-2-img-1',
        'http://img.example.com/img22': 'test-2-img-2',
        'http://img.example.com/img23': 'test-2-img-3'
    }
)

pkg3 = ModelPackage(
    name='package-3',
    description='My third test package.',
    short_description='3 package.',
    owner='Tester',
    authors=['Tester', 'Nyemst'],
    license='mylicense-3',
    tags=['aaa', 'ccc', 'zzz'],
    versions={
        '1.2.0': {
            'files': {
                'http://example.com/file37': {
                    'dir': '/bin',
                    'name': 'test-3-file-7'
                },
                'http://example.com/file38': {
                    'dir': '/lib',
                    'name': 'test-3-file-8'
                },
                'http://example.com/file39': {
                    'dir': '/man',
                    'name': 'test-3-file-9'
                }
            },
            'depends': {
                'dpackage-7': {
                    'version': '~1.12.51',
                    'type': 'required'
                },
                'dpackage-8': {
                    'version': '^3.5',
                    'type': 'optional'
                },
                'dpackage-9': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 33.'
        },
        '1.1.0': {
            'files': {
                'http://example.com/file34': {
                    'dir': '/bin',
                    'name': 'test-3-file-4'
                },
                'http://example.com/file35': {
                    'dir': '/lib',
                    'name': 'test-3-file-5'
                },
                'http://example.com/file36': {
                    'dir': '/man',
                    'name': 'test-3-file-6'
                }
            },
            'depends': {
                'dpackage-7': {
                    'version': '~1.12.51',
                    'type': 'required'
                },
                'dpackage-8': {
                    'version': '^3.5',
                    'type': 'optional'
                },
                'dpackage-9': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 32.'
        },
        '1.0.0': {
            'files': {
                'http://example.com/file31': {
                    'dir': '/bin',
                    'name': 'test-3-file-1'
                },
                'http://example.com/file32': {
                    'dir': '/lib',
                    'name': 'test-3-file-2'
                },
                'http://example.com/file33': {
                    'dir': '/man',
                    'name': 'test-3-file-3'
                }
            },
            'depends': {
                'dpackage-7': {
                    'version': '~1.12.51',
                    'type': 'required'
                },
                'dpackage-8': {
                    'version': '^3.5',
                    'type': 'optional'
                },
                'dpackage-9': {
                    'version': '*',
                    'type': 'recommended'
                }
            },
            'changes': 'Change 31.'
        }
    },
    screenshots={
        'http://img.example.com/img31': 'test-3-img-1',
        'http://img.example.com/img32': 'test-3-img-2',
        'http://img.example.com/img33': 'test-3-img-3'
    }
)
