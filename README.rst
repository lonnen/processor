=========================================
Jansky: A Breakpad crash report processor
=========================================

Built to accept crashes collected by `Antenna
<https://github.com/mozilla/antenna>`_, applies JSON/dump pairs to the
stackwalk_server application, parses the output, and records the results.
Jansky, coupled with stackwalk_server, is computationally intensive. Multiple
instances of Jansky can be run simultaneously.

:Free software: Mozilla Public License version 2.0
:Documentation: https://processor.readthedocs.io/
:Status:        Pre-alpha


Quickstart
==========


This is a quickstart that uses Docker so you can see how the pieces work. Docker
is also used for local development of Jansky.

For more comprehensive documentation or instructions on how to set this up in
production, see docs_.

1. Clone the repository:

   .. code-block:: shell

      $ git clone https://github.com/mozilla/jansky/


2. `Install docker 1.10.0+ <https://docs.docker.com/engine/installation/>`_ and
   `install docker-compose 1.6.0+ <https://docs.docker.com/compose/install/>`_
   on your machine

3. Download and build Processor docker containers:

   .. code-block:: shell

      $ make build


   Anytime you want to update the containers, you can run ``make build``.

4. Run with a prod-like fully-functional configuration.

   1. Running:

      .. code-block:: shell

         $ make run


   2. Verify things are running:

      In another terminal, you can verify the proper containers are running with
      ``docker ps``.

   3. Look at runtime metrics with Grafana:

      The ``statsd`` container has `Grafana <https://grafana.com/>`_. You can view
      the statsd data via Grafana in your web browser `<http://localhost:9000>`_.

      To log into Grafana, use username ``admin`` and password ``admin``.

      You'll need to set up a Graphite datasource pointed to
      ``http://localhost:8000``.

   4. Shutting down Jansky:

      When you're done with the Jansky process, hit CTRL-C to gracefully kill
      the docker container.


   If you want to run with a different Jansky configuration, put the
   configuration in an env file and then set ``JANSKY_ENV``. For example:

   .. code-block:: shell

      $ JANSKY_ENV=my.env make run


   See ``prod.env`` and the docs_ for configuration options.

5. Run tests:

   .. code-block:: shell

      $ make test


   If you need to run specific tests or pass in different arguments, you can run
   bash in the base container and then run ``py.test`` with whatever args you
   want. For example:

   .. code-block:: shell

      $ make shell
      app@...$ py.test

      <pytest output>

      app@...$ py.test tests/unittest/test_crashstorage.py


   We're using py.test_ for a test harness and test discovery.


For more details on running Jansky or hacking on Jansky, see the docs_.

.. _py.test: http://pytest.org/
.. _docs: https://jansky.readthedocs.io/
