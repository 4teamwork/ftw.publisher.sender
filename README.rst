Introduction
============

The `ftw.publisher` packages provide tools for publishing plone contents from
one instance to another.

By providing a simple mechanism to invoke the publishing, it's possible to
set up the publisher in a variety of ways, such as workflow bound, manually
invoked or automated publication.

The `ftw.publisher` package library also provides a variety of surveillance
and analysis tools for making maintenance confortable.


Staging
=======

The `ftw.publisher` is meant to be used in a environment where there are two
seperate plone-sites which do not share their database. The editors work on
a **editorial site** and the contents are published to a **public site** when
they are ready. Setting up such an environment with `ftw.publisher` let you
have a powerful staging solution with completly isolated instances.


Network security
================

Using an environment with two isolated installations makes it possible to
protect the editorial site with firewalls or to put it even in a private
company network. This way the editorial site is completly protected from
the internet, which is in some use cases mandatory for protecting other -
unpublished - contents (for example when publishing the internet contents
from the intranet).


Component support
=================

- Archetypes objects
- Standard Archetypes field types
- Topics: criterias are published automatically when topic is published
- Backreferences - references are added automatically as soon both objects
  are published
- Additional interfaces added on /manage_interfaces or by other products
- Contextual portlets
- Properties

With the publisher adapter structure it is as easy as creating another
adapter to support other components. For instance annotations are not supported
by design, because you may not wan't to publish all annotations but only
certain ones. Therefore it is easyer to implement custom adapters for
those annotations which need to be published.


Packages
========

*Mandatory packages:*

ftw.publisher.sender
  The sender package provides a configuration panel and is responsible for
  sending contents to the target instance. It's usually installed on a
  **editorial site**.
  `ftw.publisher.sender source <https://github.com/4teamwork/ftw.publisher.sender>`_ |
  `ftw.publisher.sender pypi <http://pypi.python.org/pypi/ftw.publisher.sender>`_

ftw.publisher.receiver
  The receiver package is installed on the **public site** and is the target
  of the publishing process. It has tools for receiving a request and creating,
  updating or deleting objects which should be published or retrieved.
  `ftw.publisher.receiver source <https://github.com/4teamwork/ftw.publisher.receiver>`_ |
  `ftw.publisher.receiver pypi <http://pypi.python.org/pypi/ftw.publisher.receiver>`_

ftw.publisher.core
  The core package is installed on both, sender and receiver instances. It
  provides adapters for serializing and unserializing components of plone
  contents (such as portlets).
  `ftw.publisher.core source <https://github.com/4teamwork/ftw.publisher.core>`_ |
  `ftw.publisher.core pypi <http://pypi.python.org/pypi/ftw.publisher.core>`_


*Optional packages:*

ftw.publisher.example
  This example package provides a publisher-bound workflow and shows how to
  write an integration package for this use case.
  `ftw.publisher.example source <https://github.com/4teamwork/ftw.publisher.example>`_ |
  `ftw.publisher.example pypi <http://pypi.python.org/pypi/ftw.publisher.example>`_


Installation & Usage
====================

Take a look at the
`ftw.pubisher.example <https://github.com/4teamwork/ftw.publisher.example>`_
package and the
`example buildout <https://github.com/4teamwork/ftw.publisher-example-buildout>`_.
See also the `wiki https://github.com/4teamwork/ftw.publisher.sender/wiki`_.


Links
=====

The main project package is `ftw.publisher.sender` since it contains all the
configuration panels and the most tools - but without the other mandatory
packages it will not work.
Here are some additional links:

- Publisher packages on pypi: http://pypi.python.org/pypi?%3Aaction=search&term=ftw.publisher&submit=search
- Main github project repository: https://github.com/4teamwork/ftw.publisher.sender
- Issue tracker: https://github.com/4teamwork/ftw.publisher.sender/issues
- Wiki: https://github.com/4teamwork/ftw.publisher.sender/wiki


Credits
=======

Sponsored by `4teamwork GmbH <http://www.4teamwork.ch/>`_.

Authors:

- `jone <http://github.com/jone>`_
- `maethu <https://github.com/maethu>`_
