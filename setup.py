from setuptools import setup, find_packages
import os

version = open('ftw/publisher/sender/version.txt').read().strip()
maintainer = 'Jonas Baumann'

tests_require = [
    'collective.testcaselayer',
    ]

setup(name='ftw.publisher.sender',
      version=version,
      description="Sender package for publisher product" + \
          ' (Maintainer: %s)' % maintainer,
      long_description=open("README.txt").read() + "\n" + \
          open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='publisher sender',
      author='%s, 4teamwork GmbH' % maintainer,
      author_email='mailto:info@4teamwork.ch',
      url='http://psc.4teamwork.ch/4teamwork/ftw/ftw.publisher.sender',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['ftw'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'setuptools',
        # -*- Extra requirements: -*-
        'plone.z3cform',
        'simplejson',
        'z3c.autoinclude',
        'z3c.form',
        ],
      extras_require={
        'tests_require': tests_require,
        },
      tests_require=tests_require,
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
