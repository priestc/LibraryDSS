from setuptools import setup, find_packages

setup(
    name='ldss',
    version='0.1.0',
    description='',
    long_description=open('README.md').read(),
    author='',
    author_email='',
    url='',
    packages=find_packages(),
    include_package_data=True,
    license='LICENSE',
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    dependency_links=[
        "https://github.com/priestc/python-lql/tarball/master#egg=python-lql-0.1.0"
    ],
    install_requires=[
        #'giotto==0.11.0',
        'python-lql',
        'python-dateutil==1.5',
        'psycopg2',
        'iso8601',
        'boto',
        'filechunkio',
        'dropbox',
        'google-api-python-client',
    ],
)