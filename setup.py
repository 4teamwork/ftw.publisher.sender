from setuptools import setup, find_packages
import os

version = '2.7.8'
maintainer = 'Jonas Baumann'

tests_require = [
    'collective.testcaselayer',
    'Products.PloneFormGen < 1.8.0a',  # Plone 4 Version
    'plone.app.referenceablebehavior',
    'plone.app.relationfield',
    'plone.app.testing',
    'Products.PloneTestCase',
    'ftw.testing [splinter]',
    'ftw.testbrowser',
    'ftw.lawgiver',
    'ftw.builder',
    'ftw.contentpage',
    'ftw.simplelayout [contenttypes]',
    'zc.relation',
    ]


setup(name='ftw.publisher.sender',
      version=version,
      description="Staging and publishing addon for Plone contents.",
      long_description=open("README.rst").read() + "\n" + \
          open(os.path.join("docs", "HISTORY.txt")).read(),

      # Get more strings from
      # http://www.python.org/pypi?%3Aaction=list_classifiers

      classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 4.2',
        'Framework :: Plone :: 4.3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

      keywords='publisher sender',
      author='4teamwork AG',
      author_email='mailto:info@4teamwork.ch',
      maintainer=maintainer,
      url='https://github.com/4teamwork/ftw.publisher.sender',
      license='GPL2',

      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw', 'ftw.publisher'],
      include_package_data=True,
      zip_safe=False,

      install_requires=[
        'setuptools',

        'AccessControl',
        'Acquisition',
        'zExceptions',
        'transaction',
        'zope.annotation',
        'zope.component',
        'zope.event',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.publisher',
        'zope.schema',
        'zope.viewlet',
        'ZODB3',
        'Zope2',

        'Plone',
        'plone.memoize',
        'Products.ZCatalog',
        'Products.statusmessages',
        'Products.CMFCore',
        'Products.CMFPlone',

        'ftw.autofeature',
        'ftw.publisher.core >= 2.6.0',
        'ftw.profilehook',
        'ftw.table',
        'ftw.upgrade',
        'z3c.form',
        'zc.queue<2',
        'plone.z3cform',
        ],

      extras_require={
        'tests': tests_require,
        'PloneFormGen': ['Products.PloneFormGen'],
        'development': ['ftw.lawgiver'],
        'taskqueue': ['collective.taskqueue'],
        },

      tests_require=tests_require,

      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
