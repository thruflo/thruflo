from setuptools import setup, find_packages

setup(
    name = 'thruflo',
    version = '0.3.1',
    description = 'Generate documents from markdown files in a github repository',
    long_description = open('README.md').read(),
    author = 'James Arthur',
    author_email = 'thruflo@googlemail.com',
    url = 'http://github.com/thruflo/thruflo',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Programming Language :: Python'
    ],
    license = open('LICENSE.md').read(),
    packages = ['thruflo'],
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe = False,
    install_requires=[
        'setuptools_git==0.3.4',
        'simplejson>=2.0.9',
        'Mako>=0.3.2',
        'Beaker>=1.5.3',
        'couchdbkit>=0.4.6',
        'greenlet>=0.2',
        'gevent',
        'gunicorn>=0.9.1',
        'redis>=1.36',
        'FormEncode>=1.2.2',
        'webob>=0.9.8',
        'github2',
        'oauth2>=1.1.3',
    ],
    entry_points = {
        'setuptools.file_finders': [
            "foobar = setuptools_git:gitlsfiles"
        ],
        'console_scripts': [
            'thruflo-sync = thruflo.model:sync'
        ]
    }
)
