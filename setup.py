from setuptools import setup, find_packages

setup(
    name = 'thruflo',
    version = '0.3.2',
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
        'couchdbkit>=0.4.6',
        'greenlet>=0.2',
        'gevent',
        'Paste>=1.7.3',
        'PasteDeploy>=1.3.3',
        'PasteScript>=1.7.3',
        'gunicorn>=0.9.1',
        'thruflo.webapp>=0.1',
        'FormEncode>=1.2.2',
        'pyDNS>=2.3.4',
        'Markdown>=2.0.3'
    ],
    entry_points = {
        'setuptools.file_finders': [
            "foobar = setuptools_git:gitlsfiles"
        ],
        'paste.app_factory': [
            'main=thruflo.main:app_factory',
        ],
        'console_scripts': [
            'thruflo-sync = thruflo.model:sync',
            'relay-payload = thruflo.test:relay_commit_payload'
        ]
    }
)
