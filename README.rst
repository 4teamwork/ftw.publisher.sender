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

Core packages
-------------

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


Addon packages
--------------

ftw.publisher.example
  This example package provides a publisher-bound workflow and shows how to
  write an integration package for this use case.
  `ftw.publisher.example source <https://github.com/4teamwork/ftw.publisher.example>`_ |
  `ftw.publisher.example pypi <http://pypi.python.org/pypi/ftw.publisher.example>`_

ftw.publisher.monitor
  Sends alert mails when the publisher queue is blocked and publishing does no
  longer work.
  `ftw.publisher.monitor source <https://github.com/4teamwork/ftw.publisher.monitor>`_ |
  `ftw.publisher.monitor pypi <http://pypi.python.org/pypi/ftw.publisher.monitor>`_

ftw.publisher.mailreport
  Sends scheduled reports about the publishing state (executed jobs, failed jobs, etc.).
  `ftw.publisher.mailreport source <https://github.com/4teamwork/ftw.publisher.mailreport>`_ |
  `ftw.publisher.mailreport pypi <http://pypi.python.org/pypi/ftw.publisher.mailreport>`_

ftw.publisher.controlling
  Views for comparing the editorial and the public site. Detects inconsistencies and problems
  by comparing the catalogs of the two sites. Useful in workflow based publishing environments.
  `ftw.publisher.controlling source <https://github.com/4teamwork/ftw.publisher.controlling>`_ |
  `ftw.publisher.controlling pypi <http://pypi.python.org/pypi/ftw.publisher.controlling>`_



Installation & Usage
====================

Take a look at the
`ftw.pubisher.example <https://github.com/4teamwork/ftw.publisher.example>`_
package and the
`example buildout <https://github.com/4teamwork/ftw.publisher-example-buildout>`_.
See also the `wiki <https://github.com/4teamwork/ftw.publisher.sender/wiki>`_.


Override realm configuration with ZCML
--------------------------------------

The realms are by default configured in the database through the control panel.
When copying the database from a production environment to a staging environment
the realm configuration is copied too, which could result in publishing from
the staging editorial site to the production public site, which is very bad.

For solving this issue it is possible to override the realm configuration with
ZCML, so that it can be configured also using the ``zcml-additional`` option of
the buildout.

.. code:: xml

    <configure xmlns:publisher="http://namespaces.zope.org/ftw.publisher">

        <include package="ftw.publisher.sender" file="meta.zcml" />

        <publisher:override-realm
            url="http://localhost:9090/site"
            username="publisher-user"
            password="publisher-password" />

    </configure>


Configure workflows to publish
==============================

The `ftw.publisher` can be used with workflows. For using it with workflows
you need to configure your workflow to use publisher actions and you need
to provide a configuration for your workflow, telling the publisher what each
state and transition means.

Defining a publisher configuration
----------------------------------

A publisher configuration is a simple `IWorkflowConfiguration` adapter, which
could look like this:

.. code:: python

    from ftw.publisher.sender.workflows import interfaces
    from zope.component import adapts
    from zope.interface import Interface
    from zope.interface import implements


    class MyWorkflowConfiguration(object):
        implements(interfaces.IWorkflowConfiguration)
        adapts(Interface)

        def __init__(self, request):
            self.request = request

        def states(self):
            return {
                'private': None,
                'pending': None,
                'published': interfaces.PUBLISHED,
                'revision': interfaces.REVISION}

        def transitions(self):
            return {
                'submit': interfaces.SUBMIT,
                'publish': interfaces.PUBLISH,
                'reject': interfaces.RETRACT,
                'retract': interfaces.RETRACT,
                'revise': None}

The *named*-adapter is then registered with some ZCML, where the name
of the adapter is the ID of the workflow in portal_workflow.

.. code:: xml

    <adapter factory=".config.MyWorkflowConfiguration"
             name="my-workflow" />

**Lawgiver-Workflows**

`ftw.lawgiver <https://github.com/4teamwork/ftw.lawgiver>`_ is a tool for
writing workflows. If you are using the lawgiver, you can use
`LawgiverWorkflowConfiguration` as a base class, which allows you to define
the states and transitions by name / statement instead of ID:

.. code:: python

    from ftw.publisher.sender.workflows import config
    from ftw.publisher.sender.workflows import interfaces


    class ExampleWorkflowConfiguration(config.LawgiverWorkflowConfiguration):
        workflow_id = 'publisher-example-workflow'

        def lawgiver_states(self):
            return {
                'Internal': None,
                'Pending': None,
                'Published': interfaces.PUBLISHED,
                'Revision': interfaces.REVISION}

        def lawgiver_transitions(self):
            return {
                'submit (Internal => Pending)': interfaces.SUBMIT,
                'publish (Internal => Published)': interfaces.PUBLISH,
                'reject (Pending => Internal)': None,
                'publish (Pending => Published)': interfaces.PUBLISH,
                'retract (Published => Internal)': interfaces.RETRACT,
                'revise (Published => Revision)': None,
                'publish (Revision => Published)': interfaces.PUBLISH,
                }


Transition validation (constraints)
-----------------------------------

When a user publishes a content and its container is not yet published it
will fail on the remote system, because the container is missing.

The publisher provides workflow constraints for prohibiting bad transitions
and for warning when something should be done (e.g. references should also
be published).

You should enable those constraints for your workflow by changing the
transition action URL ("Display in actions box" -> "URL (formatted)") to
the format ``%(content_url)s/publisher-modify-status?transition=TRANSITION``
(replace ``TRANSITION``) with the transition ID.
The default Plone URL is
``%(content_url)s/content_status_modify?workflow_action=TRANSITION``.

The constraints are adapters registered for each workflows. This allows
to change the constraints per workflow easily. Take a look at the
`publisher example workflow constraints <https://github.com/4teamwork/ftw.publisher.sender/blob/master/ftw/publisher/sender/workflows/example.py>`_.

You might either subclass the example workflow constraint and extend it,
write your own constraint definitions from scratch or directly use the
example workflow constraints for your workflow.

Reusing the example workflow constraints is as simple as registering a
named adapter (your workflow ID in portal_workflow is the name of the
adapter):

.. code:: xml

    <adapter factory="ftw.publisher.sender.workflows.example.ExampleWorkflowConstraintDefinition"
             name="my-workflow" />


Testing workflows
-----------------

For automatically testing whether your worlfow configuration is correct
you can reuse the publisher
`example workflow configuration tests <https://github.com/4teamwork/ftw.publisher.sender/blob/master/ftw/publisher/sender/tests/test_example_workflow_config.py>`:

.. code:: python

    from ftw.publisher.sender.tests import test_example_workflow_config
    from my.package.testing import MY_INTEGRATION_TESTING

    class TestMyWorkflowConfig(test_example_workflow_config.TestWorkflowConfig):
        layer = MY_INTEGRATION_TESTING
        workflow_id = 'my-workflow'

If you write custom constraints you should also take at the
`example constraints tests <https://github.com/4teamwork/ftw.publisher.sender/blob/master/ftw/publisher/sender/tests/test_example_workflow_constraint_definition.py>`_.


Links
=====

The main project package is `ftw.publisher.sender` since it contains all the
configuration panels and the most tools - but without the other mandatory
packages it will not work.
Here are some additional links:

- Publisher packages on pypi: http://pypi.python.org/pypi?%3Aaction=search&term=ftw.publisher&submit=search
- Github: https://github.com/4teamwork/ftw.publisher.sender
- Issues: https://github.com/4teamwork/ftw.publisher.sender/issues
- Wiki: https://github.com/4teamwork/ftw.publisher.sender/wiki
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.publisher.sender


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.publisher.sender`` is licensed under GNU General Public License, version 2.
