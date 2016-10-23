from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

# TODO: build this including dependencies

setup(name='educube',
      version='0.0.1',
      description='EduCube Tool',
      long_description=readme(),
      url='http://docs.gavip.science',
      author='UCD',
      author_email='daniel.vagg@gmail.com',
      license='LGPL',
      packages=find_packages(),
      install_requires=[
        'click',
        'markdown',
        'requests',
        'pygments',
        'tabulate',
        'tornado',
        'html5lib<=0.9999999'
      ],
      tests_require=[
        'nose',
      ],
      entry_points={
        'console_scripts': [
          'educube = educube.client:cli',
        ],
      },
      dependency_links=[
      ],
      test_suite='nose.collector',
      zip_safe=False)
