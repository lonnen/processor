Processor: A Breakpad crash report processor
============================================

[![Build Status](https://travis-ci.org/mozilla/processor.svg?branch=master)](https://travis-ci.org/mozilla/processor)

Development Status :: 2 - Pre-Alpha

Built to accept crashes collected by [Antenna](https://github.com/mozilla/antenna), applies JSON/dump pairs to the stackwalk_server application, parses the output, and records the results. The processor, coupled with stackwalk_server, is computationally intensive. Multiple instances of the processor can be run simultaneously.

* Free software: Mozilla Public License version 2.0


Quickstart
==========


This is a quickstart that uses Docker so you can see how the pieces work. Docker
is also used for local development of Processor.

For more comprehensive documentation or instructions on how to set this up in
production, see docs_.

1. Clone the repository:

   .. code-block:: shell

      $ git clone https://github.com/mozilla/processor


2. `Install docker 1.10.0+ <https://docs.docker.com/engine/installation/>`_ and
   `install docker-compose 1.6.0+ <https://docs.docker.com/compose/install/>`_
   on your machine

3. Download and build Processor docker containers:

   .. code-block:: shell

      $ make build


   Anytime you want to update the containers, you can run ``make build``.

4. Run with a prod-like fully-functional configuration:

   .. code-block:: shell

      $ make run


   You should see a lot of output. It'll start out with something like this::

      PROCESSOR_ENV="prod.env" /usr/bin/docker-compose up web


   In another terminal, you can verify the proper containers are running with
   ``docker ps``.

   When you're done with the Processor process, hit CTRL-C to gracefully kill
   the docker web container.

   If you want to run with a different Processor configuration, put the
   configuration in an env file and then set ``PROCESSOR_ENV``. For example:

   .. code-block:: shell

      $ PROCESSOR_ENV=my.env make run


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


For more details on running Processor or hacking on Processor, see the docs_.

.. _py.test: http://pytest.org/
.. _docs: TODO
