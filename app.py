import os

from pyramid.paster import get_app
from pyramid.paster import get_appsettings


here = os.path.dirname(os.path.abspath(__file__))

# are we on OPENSHIFT?
config = os.path.join(here, 'production.ini')

# find 'main' method in __init__.py. That is our wsgi app
app = get_app(config, 'main')
# don't really need this but is an example on how to get settings
# from the '.ini' files
settings = get_appsettings(config, 'main')
