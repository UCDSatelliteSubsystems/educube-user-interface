from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='educube',
      version='0.5.8',
      download_url='https://github.com/ezeakeal/educube_client/tarball/0.5.8',
      keywords=['educube'],
      description='EduCube Client',
      long_description=readme(),
      author='UCD',
      author_email='daniel.vagg@gmail.com',
      license='GPLv3',
      packages=find_packages(),
      include_package_data = True,
      install_requires=[
        'click',
        'markdown',
        'pygments',
        'pyserial',
        'requests',
        'tabulate',
        'tornado',
      ],
      tests_require=[
        'nose',
      ],
      entry_points={
        'console_scripts': [
          'educube = educube.client:main',
        ],
      },
      dependency_links=[
      ],
      test_suite='nose.collector',
      zip_safe=False)
