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

        r = Rule()

        # intended for testing only
        if r.predicate(
            'AAAAAAAA-1111-4242-FFFB-094F01B8FF11',
            get_raw_crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11'),
            get_dumps('AAAAAAAA-1111-4242-FFFB-094F01B8FF11'),
            get_processed_crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
        ):
            r.action(
                'AAAAAAAA-1111-4242-FFFB-094F01B8FF11',
                get_raw_crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11'),
                get_dumps('AAAAAAAA-1111-4242-FFFB-094F01B8FF11'),
                get_processed_crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
            )

        # better for application code
        r(
            'AAAAAAAA-1111-4242-FFFB-094F01B8FF11',
            get_raw_crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11'),
            get_dumps('AAAAAAAA-1111-4242-FFFB-094F01B8FF11'),
            get_processed_crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
        )


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
        logger.info((crash_id, raw_crash, dumps, processed_crash))


class UUIDCorrection(Rule):
    '''set the UUID in the raw_crash if it is missing

    from the ProcessorApp._transform method, where this happens after loading
    but before any transform rules are applied. refactoring it out to a
    transform rule.

    TODO: should this be an error condition instead?
    '''
    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        return 'uuid' not in raw_crash

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        raw_crash['uuid'] = crash_id
