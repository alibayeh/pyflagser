#! /usr/bin/env python
"""Python bindings for the flagser C++ library."""

import os
import codecs
import re
import sys
import platform
import subprocess

from pkg_resources.extern.packaging import version
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext


PACKAGE_DIR = "pyflagser"

version_file = os.path.join(PACKAGE_DIR, "_version.py")
with open(version_file) as f:
    exec(f.read())

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

DISTNAME = 'pyflagser'
DESCRIPTION = 'Python bindings for the flagser C++ library.'
with codecs.open('README.rst', encoding='utf-8-sig') as f:
    LONG_DESCRIPTION = f.read()
LONG_DESCRIPTION_TYPE = 'text/x-rst'
MAINTAINER = 'Guillaume Tauzin, Umberto Lupo'
MAINTAINER_EMAIL = 'maintainers@giotto.ai'
URL = 'https://github.com/alibayeh/pyflagser'
LICENSE = 'GNU AGPLv3'
VERSION = __version__  # noqa
# DOWNLOAD_URL = f"https://github.com/giotto-ai/pyflagser/tarball/v{VERSION}"
DOWNLOAD_URL = f"https://github.com/alibayeh/pyflagser/archive/refs/heads/master.zip"
VERSION = __version__ # noqa
CLASSIFIERS = ['Intended Audience :: Science/Research',
               'Intended Audience :: Developers',
               'License :: OSI Approved',
               'Programming Language :: C++',
               'Programming Language :: Python',
               'Topic :: Software Development',
               'Topic :: Scientific/Engineering',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: POSIX',
               'Operating System :: Unix',
               'Operating System :: MacOS',
               'Programming Language :: Python :: 3.7',
               'Programming Language :: Python :: 3.8',
               'Programming Language :: Python :: 3.9',
               'Programming Language :: Python :: 3.10']
KEYWORDS = 'topological data analysis, persistent ' + \
    'homology, directed flags complex, persistence diagrams'
INSTALL_REQUIRES = requirements
EXTRAS_REQUIRE = {'tests': ['pytest',
                            'pytest-timeout',
                            'pytest-cov',
                            'pytest-azurepipelines',
                            'pytest-benchmark',
                            'flake8'],
                  'doc': ['sphinx',
                          'sphinx-gallery',
                          'sphinx-issues',
                          'sphinx_rtd_theme',
                          'numpydoc']}


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the "
                               " following extensions: " +
                               " , ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = version.parse(re.search(r'version\s*([\d.]+)',
                                                    out.decode()).group(1))
            if cmake_version < version.parse("3.1.0"):
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        self.install_dependencies()

        for ext in self.extensions:
            self.build_extension(ext)

    def install_dependencies(self):
        dir_start = os.getcwd()
        dir_pybind11 = os.path.join(dir_start, 'pybind11')
        if os.path.exists(dir_pybind11):
            return 0
        os.mkdir(dir_pybind11)
        subprocess.check_call(['git', 'clone',
                               'https://github.com/pybind/pybind11.git',
                               dir_pybind11])
        subprocess.check_call(['git', 'submodule', 'update',
                               '--init', '--recursive'])

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.join(os.path.dirname(
            self.get_ext_fullpath(ext.name)), 'pyflagser', 'modules'))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(
                cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j2']

        if sys.platform.startswith("darwin"):
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += \
                    ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get('CXXFLAGS', ''), self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args,
                              cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args,
                              cwd=self.build_temp)


setup(name=DISTNAME,
      maintainer=MAINTAINER,
      maintainer_email=MAINTAINER_EMAIL,
      description=DESCRIPTION,
      license=LICENSE,
      url=URL,
      version=VERSION,
      download_url=DOWNLOAD_URL,
      long_description=LONG_DESCRIPTION,
      long_description_content_type=LONG_DESCRIPTION_TYPE,
      zip_safe=False,
      classifiers=CLASSIFIERS,
      packages=find_packages(),
      keywords=KEYWORDS,
      install_requires=INSTALL_REQUIRES,
      extras_require=EXTRAS_REQUIRE,
      ext_modules=[CMakeExtension('pyflagser')],
      cmdclass=dict(build_ext=CMakeBuild))
