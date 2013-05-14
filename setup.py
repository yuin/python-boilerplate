#vim: fileencoding=utf8
from __future__ import division, print_function
import re, sys, os, codecs, itertools
from os.path import join, abspath, dirname, exists, basename
from subprocess import Popen, PIPE
from contextlib import contextmanager

from setuptools import setup
from distutils.core import Command
import distutils.command as scommands

ROOT_DIR = dirname(abspath(__file__))
PACKAGE  = basename(ROOT_DIR)
if exists(join(ROOT_DIR, "boilerplate")):
  os.rename(join(ROOT_DIR, "boilerplate"), join(ROOT_DIR, PACKAGE))

# compatibility stuff {{{ 
if sys.version_info >= (3,0,0):
  unicode = str
  string_types = (unicode, bytes)
  def n_(s):
    if isinstance(s, unicode): return s
    elif isinstance(s, bytes): return s.decode("latin1")
    return unicode(s)
  getcwd = os.getcwd
else:
  bytes = str
  string_types = basestring
  def n_(s):
    if isinstance(s, bytes): return s
    elif isinstance(s, unicode): return s.encode("latin1")
    return bytes(s)
  getcwd = os.getcwdu

def b_(s, encoding='utf8'):
  if isinstance(s, unicode): return s.encode(encoding) 
  elif isinstance(s, (integer_types + (float,))): return b_(repr(s))
  return bytes(s)
def u_(s, encoding='utf8', errors='strict'):
  return s.decode(encoding, errors) if isinstance(s, bytes) else unicode(s)
# }}}

# extra commands support {{{
class _Odict(dict): keys = lambda self: sorted(dict.keys(self))
_va = dict(cmd_args={}, nssep="_")
_cmds = _Odict()
_namespace = []
_old_scommands = scommands.__all__[:]

_get_ns = lambda:_namespace and _va["nssep"].join(_namespace)+_va["nssep"] or ""
class _CommandType(type):
  def __new__(cls, class_name, class_bases, classdict):
    d = dict(user_options=[], finalize_options=lambda s:None)
    d.update(classdict)
    def _(self):
      [setattr(self,i[0].rstrip("="),None) for i in d["user_options"]]
    d["initialize_options"] = _
    d["boolean_options"] = [i for i,j,k in d["user_options"] if not i.endswith("=")]
    def _(self):
      for v in self.get_sub_commands(): self.run_command(v)
      return classdict["run"](self)
    d["run"] = _
    name = _get_ns()+class_name.lower()
    cls = type.__new__(cls, name, class_bases + (object,), d)
    cls.description = cls.__doc__ and cls.__doc__.strip() or ""
    if "sub_commands" in d:
      cls.description += "(sub commands:"+",".join(i for i,j in d["sub_commands"])+")"
    if name in _old_scommands and name not in scommands.__all__: scommands.__all__.append(name)
    if class_name != "Task" : _cmds[name] = cls
    return cls
Task = _CommandType('Task', (Command, ), {})

@contextmanager
def namespace(name):
  _namespace.append(name)
  yield _get_ns()
  _namespace.pop() 

# }}}

# shell utilities {{{
def xx(cmd):
  print("EXEC:(on {})".format(getcwd()), cmd)
  p = Popen(cmd, shell=True)
  p.wait()
  if p.returncode != 0:
    raise Exception("FAILED: (RET:{})".format(p.returncode))

def xc(cmd):
  print("EXEC:(on {})".format(getcwd()), cmd)
  p = Popen(cmd, shell=True, stdout=PIPE)
  p.wait()
  if p.returncode != 0:
    raise Exception("FAILED: (RET:{})".format(p.returncode))
  return p.stdout.read()

@contextmanager
def cd(dir):
  os.chdir(dir)
  print("EXEC: cd {}".format(getcwd()))
  yield

# }}}

# utilities {{{
def get_meta(name):
  path = join(ROOT_DIR, PACKAGE, "__init__.py")
  text = codecs.open(path, "r", encoding="utf8", errors="ignore").read()
  return n_(re.search(r"__%s__[\s]*=[\s]*['\"]([^'\"]+)['\"]"%name, text).group(1))

def parse_dep(dep):
  m = re.search("egg=(.*)", dep)
  return m.group(1) if m else dep

def get_deps_from_tox_ini(tests_requires = False):
  deps = []
  flag = False
  tox_ini = join(ROOT_DIR, "tox.ini")
  if not exists(tox_ini):
    return []
  for line in open(tox_ini).read().splitlines():
    if line.startswith("[testenv]"):
      flag = True
      continue
    if flag:
      if line.startswith("deps"):
        deps.append(parse_dep(line.strip().replace("deps=","")))
      elif deps:
        if not line.strip():
          break
        deps.append(parse_dep(line.strip()))

  if tests_requires:
    return list(itertools.dropwhile(lambda v:v != "pytest", deps))
  return list(itertools.takewhile(lambda v:v != "pytest", deps))
# }}}

with namespace("boilerplate") as ns: # {{{
  class init(Task): # {{{
    """initialize a project"""
    def run(self):
      def replace_package_name(file):
        print("generate {}".format(basename(file)))
        contents = open(file+".tpl").read()
        with open(file, "w") as io:
          io.write(contents.replace("{{PACKAGE}}", PACKAGE))

      with cd(ROOT_DIR):
        replace_package_name(join(ROOT_DIR, "MANIFEST.in"))
        replace_package_name(join(ROOT_DIR, ".gitignore"))
        replace_package_name(join(ROOT_DIR, "tox.ini"))
        xx("rm .*.tpl")
        xx("rm *.tpl")
        xx("rm -rf .git")
        xx("git init")

      with cd(join(ROOT_DIR, "docs", "source")):
        print("generate docs/source/{}.rst".format(PACKAGE))
        with open("{}.rst".format(PACKAGE), "w") as io:
          io.write(""".. automodule:: {}
   :members:
""".format(PACKAGE))

      with cd(ROOT_DIR):
        xx("git add .")
        xx("git commit -am 'initial commit'")

      print("")
      print("")
      print("")
      print("- next step: edit README.rst,  {}/__init__.py".format(PACKAGE))
      print("""- to push this repository to the github, run following commands:
  git remote add origin REMOTE_URL
  git push origin master
""")


  # }}}
# }}}

with namespace("doc") as ns: # {{{
  class create(Task): # {{{
    """create a document submodule.(branch gh-pages)"""
    def run(self):
      with cd(ROOT_DIR):
        xx("git checkout -b gh-pages origin/gh-pages")
        xx("git rm -rf --ignore-unmatch {}/*".format(ROOT_DIR))
        xx("git rm -rf --ignore-unmatch {}/.*".format(ROOT_DIR))
        xx("git commit -am 'create gh-pages'")
        xx("git checkout master")
        submodule = re.split("\s+", xc("git remote -v").strip().split("\n")[0])[1]
        xx("git submodule add {} {}".format(submodule, join(ROOT_DIR, "docs", "build", "html")))
        xx("git submodule init")
        xx("git submodule update")
      with cd(join(ROOT_DIR, "docs", "build", "html")):
        xx("git checkout gh-pages")
      with cd(ROOT_DIR):
        pass
  # }}}

  class init(Task): # {{{
    """init a document submodule.(branch gh-pages)"""
    def run(self):
      with cd(ROOT_DIR):
        xx("git submodule init")
        xx("git submodule update")
      with cd(join(ROOT_DIR, "docs", "build", "html")):
        xx("git checkout gh-pages")
  # }}}

  class generate(Task): # {{{
    """generate documents.""" 
    def run(self):
      with cd(ROOT_DIR):
        current_branch = xx("git branch | grep '*' | cut -d' ' -f 2").strip()
      with cd(join(ROOT_DIR, "docs", "build", "html")):
        xx("git checkout gh-pages")
      with cd(ROOT_DIR):
        xx("sphinx-build -d docs/build/doctrees -b html docs/source docs/build/html")
      with cd(join(ROOT_DIR, "docs", "build", "html")):
        xx("git status")
      with cd(ROOT_DIR): 
        pass

      print("""to commit documents, run following commands:
  cd {}
  git commit -am "update docs"
  git push origin gh-pages
  cd {}
  git commit -am "update gh-pages submodule"
  git push origin {}
""".format(join(ROOT_DIR, "docs", "build", "html"), ROOT_DIR, current_branch))

    sub_commands = [
      ("build", None),
      ("install", None)
    ]
  # }}}
# }}}

# test(by py.test) {{{
from setuptools.command.test import test as TestCommand
class test(Task, TestCommand):
  """run unit tests after in-place build"""
  def run(self):
    import pytest
    self.test_args = ["-rxs", "--cov-report", "term-missing", "--cov", PACKAGE, "tests"]
    self.test_suite = True
    pytest.main(self.test_args)

  sub_commands = [
    ("build", None),
    ("install", None)
  ]
# }}}
  
# setup {{{
development_statuses = [None,
  "Development Status :: 1 - Planning",
  "Development Status :: 2 - Pre-Alpha",
  "Development Status :: 3 - Alpha",
  "Development Status :: 4 - Beta",
  "Development Status :: 5 - Production/Stable",
  "Development Status :: 6 - Mature",
  "Development Status :: 7 - Inactive"
]

long_description = open(join(ROOT_DIR, 'README.rst'), 'r').read()
spec = dict(
  name=PACKAGE,
  version=get_meta("version"),
  description=long_description.split("\n")[0],
  long_description=long_description,
  author=get_meta("author"),
  license=get_meta("license"),
  platforms=("Platform Independent",),
  packages = [PACKAGE],
  package_dir = {PACKAGE: PACKAGE},
  include_package_data=True,
  zip_safe=False,
  cmdclass=_cmds,
  classifiers = [
      "Programming Language :: Python :: 2.7",
      "Programming Language :: Python :: 3.3",
      development_statuses[3],
      'License :: OSI Approved :: MIT License',
      'Operating System :: OS Independent',
      ],
  install_requires = get_deps_from_tox_ini(tests_requires = False),
  tests_require = get_deps_from_tox_ini(tests_requires = True)
)

if __name__ == "__main__":
  setup(**spec)
# }}}

