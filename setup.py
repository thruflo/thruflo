from setuptools import setup, find_packages

setup(
    name = 'thruflo',
    version = '0.1',
    description = 'Document generation system',
    # long_description = open('README.rst').read(),
    author = 'James Arthur',
    author_email = 'thruflo@googlemail.com',
    url = 'http://github.com/thruflo/thruflo',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Programming Language :: Python'
    ],
    license = open('LICENSE.rst').read(),
    packages = ['thruflo'],
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe = False,
    install_requires=[
        'setuptools_git==0.3.4',
        'simplejson>=2.0.9',
        'grizzled>=0.9.3',
        'Mako>=0.3.2',
        'Beaker>=1.5.3',
        'couchdbkit>=0.4.6',
        'SQLAlchemy>=0.6.0',
        #'greenlet>=0.2',
        #'gevent>=0.12.2',
        #'redis>=0.6.1',
        'FormEncode>=1.2.2',
        'pyDNS>=2.3.4',
        'pytz',
        #'BeautifulSoup==3.0.8',
    ],
    entry_points = {
        'setuptools.file_finders': [
            "foobar = setuptools_git:gitlsfiles"
        ],
        'console_scripts': [
            'daemonize = thruflo.daemonize:main',
            'thruflo = thruflo.webapp:main',
            'sync = thruflo.model:main'
        ]
    }
)