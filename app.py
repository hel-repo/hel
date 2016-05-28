import os

from pyramid.paster import get_app
from pyramid.paster import get_appsettings


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))

    if 'OPENSHIFT_APP_NAME' in os.environ:                        #are we on OPENSHIFT?
        ip = os.environ['OPENSHIFT_PYTHON_IP']
        port = int(os.environ['OPENSHIFT_PYTHON_PORT'])
        config = os.path.join(here, 'production.ini')
    else:
        ip = '0.0.0.0'                                            #localhost
        port = 6543
        config = os.path.join(here, 'development.ini')

    app = get_app(config, 'main')                                 #find 'main' method in __init__.py.  That is our wsgi app
    settings = get_appsettings(config, 'main')                    #don't really need this but is an example on how to get settings from the '.ini' files

    # Waitress (remember to include the waitress server in "install_requires" in the setup.py)
    from waitress import serve
    print("Starting Waitress.")
    serve(app, host=ip, port=port, threads=50)