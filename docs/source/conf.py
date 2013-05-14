# vim: fileencoding=utf8

import sys, os
from datetime import date
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from setup import spec

release = spec["version"]
project = spec["name"]
author = spec["author"]
copyright = '{}, {}'.format(str(date.today().year), author)

# Extension
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.intersphinx']
              
intersphinx_mapping = {'http://docs.python.org/': None}
autoclass_content = "both"

# Source
master_doc = 'index'
templates_path = ['_templates']
source_suffix = '.rst'
exclude_trees = []
pygments_style = 'sphinx'

# html build settings
html_theme = 'default'

# htmlhelp settings
htmlhelp_basename = '{}doc'.format(project)

# latex build settings
latex_documents = [
    ('index', '{}.tex'.format(project), '{} Documentation'.format(project),
    author, 'manual'),
]
