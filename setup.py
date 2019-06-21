import os

from setuptools import setup, find_packages


NAME             = 'educube'
DESCRIPTION      = 'EduCube Client and User Interface'
REQUIRES_PYTHON  = '>=3.4'
KEYWORDS         = ('educube', )
LICENSE          = 'GPLv3'
INSTALL_REQUIRES = ('click', 'pyserial', 'tornado')

ENTRY_POINTS = {'console_scripts': ('educube = educube.__main__:main', )}


def version():
    _namespace = {}
    with open(os.path.join(NAME, '__version__.py')) as f:
        exec(f.read(), _namespace)

    return _namespace['__version__']


def readme():
    with open('README.rst') as f:
        return f.read()



setup(
    name                 = NAME,
    version              = version(),
    keywords             = KEYWORDS,
    description          = DESCRIPTION,
    long_description     = readme(),
    license              = LICENSE,
    packages             = find_packages(),
    include_package_data = True,
    install_requires     = INSTALL_REQUIRES,
    python_requires      = REQUIRES_PYTHON,
    entry_points         = ENTRY_POINTS,
    zip_safe             = False
)
