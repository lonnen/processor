# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from processor.util import utc_now

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


class CreateMetadata(Rule):
    '''create a metadata object hanging off the crash

    Previous processor implementations passed an explicit metadata object around
    to hold 'inside information' about the transformation process. The metadata
    object was used for a few specific things:

        processor_2015.py:187 - defined as a socorro.lib.util.DotDict()
        processor_2015.py:188 - defined processor_notes, a list starting with
                                the processor name and the class name, then
                                potentially appended to later
        processor_2015.py:192 - defined quit_check, now unecessary
        processor_2015.py:193 - defined processor = self
        processor_2015.py:194 - defined config = self.config
        processor_2015.py:200 - when reprocessing a crash, append a note with
                                the earlier processing time
        processor_2015.py:221 - define started_timestamp = self._log_job_start,
                                which wrote out that a job was starting as an
                                INFO log. Curiously, the method doensn't return
                                so I'm not sure what is being saved here,
                                exactly.
        processor_2015.py:235 - pass the metadata to a rule as an kwarg after
                                processed_crash
        processor_2015.py:250 - when any unhandled exception happens during
                                processing, append it to these notes and write
                                it to logs but otherwise try to continue
        processor_2015.py:256 - extend notes with notes from any previous
                                processing
        processor_2015.py:257 - join the notes and write them to the
                                processed_crash as 'processor_notes'

    Now quit check is removed and most of the other properties are set
    without being read. the metadata can likely be replaced with a notes object
    hung directly off the processor itself.
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        metadata = {
            'processor_notes': []
        }

        if "processor_notes" in processed_crash:
            metadata['original_processor_notes'] = [
                x.strip() for x in processed_crash['processor_notes'].split(";")
            ]

            metadata['processor_notes'].append(
                "earlier processing: %s" % processed_crash.get(
                    "started_datetime",
                    'Unknown Date'
                )
            )

        processed_crash['metadata'] = metadata
        processed_crash['success'] = False
        processed_crash['started_datetime'] = utc_now()
        processed_crash['signature'] = 'EMPTY: crash failed to process'


class SaveMetadata(Rule):
    '''records metadata about this processing event onto the processed crash

    processes the 'metadata' fields that we need to persist into top-level keys,
    and adds a completed timestamp

    this is expected to be the final rule before save
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        metadata = processed_crash['metadata']

        if 'original_processor_notes' in metadata:
            metadata['processor_notes'].extend(
                metadata['original_processor_notes'])

        processed_crash['processor_notes'] = '; '.join(
            metadata['processor_notes']
        )

        processed_crash['completed_datetime'] = utc_now()
        processed_crash['success'] = True
        # finally, delete metadata so it is not persisted anywhere
        del processed_crash['metadata']
