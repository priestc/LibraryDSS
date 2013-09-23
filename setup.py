from setuptools import setup

setup(
    name='ldss',
    version='0.1.0',
    description='',
    long_description=open('README.md').read(),
    author='',
    author_email='',
    url='',
    packages=['ldss'],
    include_package_data=True,
    license='LICENSE',
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        'giotto==0.11.0',
        'psycopg2',
        'iso8601',
        'boto',
        'filechunkio',
        'dropbox',
        'google-api-python-client',
    ],
)
