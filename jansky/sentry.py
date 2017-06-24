# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Infrastructure for optionally wrapping things in Sentry contexts to capture
unhandled exceptions

"""

import logging

from raven import Client
from raven.conf import setup_logging
from raven.handlers.logging import SentryHandler

from jansky.util import get_version_info


logger = logging.getLogger(__name__)

# Global Sentry client singleton
_sentry_client = None


def setup_sentry_logging():
    """Set up sentry logging of exceptions"""
    if _sentry_client:
        setup_logging(SentryHandler(_sentry_client))


def set_sentry_client(sentry_dsn, basedir):
    """Sets a Sentry client using a given sentry_dsn

    To clear the client, pass in something falsey like ``''`` or ``None``.

    """
    global _sentry_client
    if sentry_dsn:
        version_info = get_version_info(basedir)
        commit = version_info.get('commit')[:8]

        _sentry_client = Client(
            dsn=sentry_dsn,
            include_paths=['antenna'],
            tags={'commit': commit}
        )
        logger.info('Set up sentry client')
    else:
        _sentry_client = None
        logger.info('Removed sentry client')
