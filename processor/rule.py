# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import logging

logger = logging.getLogger(__name__)

class Rule():
    '''A callable transformation for manipulating crash state.

    For ease of testing, this base class is implemented with predicate
    and action methods. Consumers are expected to call the object directly
    in practice.

    Usage::

        from crash import crash

        crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')

        crash.fetch()
          .transform(rule1)
          .transform(rule2)
          .transform(rule_printer)
          .save()
          .errors()

    '''
    def __call__(self, crash_id, raw_crash, dumps, processed_crash):
        if self.predicate(crash_id, raw_crash, dumps, processed_crash):
            self.action(crash_id, raw_crash, dumps, processed_crash)


    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        """A test function to determine if the transformation should
        proceed. Supplied as a convenience method for testing and backwards
        compatibility. Defaults to True.

        :returns Bool: should the transformation proceed
        """
        return True

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        """The transformation to apply over the crash data. Supplied as a
        convenience method for testing and backwards compatability. Defaults
        to a noop.
        """
        return

class Identity(Rule):
    '''A noop transformation that always proceeds

    Usage::

        from crash import crash

        crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')

        crash.fetch()
          .transform(Identity)
    '''
    def __call__(self, crash_id, raw_crash, dumps, processed_crash):
        return

class Introspector(Rule):
    '''Logs the current state without transforming it'''
    def __call__(self, crash_id, raw_crash, dumps, processed_crash):
        logger.info(crash_id, raw_crash, dumps, processed_crash)
