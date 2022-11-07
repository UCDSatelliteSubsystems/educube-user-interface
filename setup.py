from setuptools import setup, find_packages
import os


NAME             = 'educube'
DESCRIPTION      = 'EduCube Client and User Interface'
REQUIRES_PYTHON  = '>=3.7'
KEYWORDS         = ('educube', )
LICENSE          = 'GPLv3'

INSTALL_REQUIRES = [
    'pyserial', 'tornado',
    'click',
]

# ****************************************************************************
# console scripts
# ****************************************************************************
CONSOLE_SCRIPTS = [
    'educube = educube.__main__:main',
]

ENTRY_POINTS = {'console_scripts': CONSOLE_SCRIPTS}

# ****************************************************************************
# version information stored in __version__.py
# ****************************************************************************
def version():
    _namespace = {}
    with open(os.path.join(NAME, '__version__.py')) as f:
        exec(f.read(), _namespace)

    return _namespace['__version__']


# ****************************************************************************
# long description from README.md
# ****************************************************************************
def readme():
    with open('README.md') as f:
        return f.read()


# ****************************************************************************
# run setup
# ****************************************************************************
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
