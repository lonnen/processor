# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
from pathlib import Path

import sys
from unittest import mock

from everett.manager import ConfigManager
import pytest


# Add repository root so we can import Processor.
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Add testlib so we can import testlib modules.
sys.path.insert(0, str(REPO_ROOT / 'tests'))

from processor.app import setup_logging # noqa
from testlib.loggingmock import LoggingMock  # noqa


def pytest_runtest_setup():
    # Make sure we set up logging to sane default values.
    setup_logging('DEBUG')


@pytest.fixture
def randommock():
    """Returns a contextmanager that mocks random.random() at a specific value

    Usage::

        def test_something(randommock):
            with randommock(0.55):
                # test stuff...

    """
    @contextlib.contextmanager
    def _randommock(value):
        with mock.patch('random.random') as mock_random:
            mock_random.return_value = value
            yield

    return _randommock

@pytest.fixture
def loggingmock():
    """Returns a loggingmock that builds a logging mock context to record logged records

    Usage::

        def test_something(loggingmock):
            with loggingmock() as lm:
                # do stuff
                assert lm.has_record(
                    name='foo.bar',
                    level=logging.INFO,
                    msg_contains='some substring'
                )


    You can specify names, too::

        def test_something(loggingmock):
            with loggingmock(['antenna', 'botocore']) as lm:
                # do stuff
                assert lm.has_record(
                    name='foo.bar',
                    level=logging.INFO,
                    msg_contains='some substring'
                )

    """
    @contextlib.contextmanager
    def _loggingmock(names=None):
        with LoggingMock(names=names) as loggingmock:
            yield loggingmock
    return _loggingmock
