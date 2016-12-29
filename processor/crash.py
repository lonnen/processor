# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from processor.rule import Identity


logger = logging.getLogger(__name__)

'''A crash object represents a single crash event

Usage::

    from rules import rule1, rule2, rule_printer

    crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')

    crash.fetch()
      .transform(rule1)
      .transform(rule2)
      .transform(rule_printer)
      .save()

'''

class Crash:
    def __init__(self, crash_id):
        '''construct a class object with a given crash_id and initialize
        other fields as empty

        :arg String crash_id: crash key for indexing

        Examples::

            Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')

        :returns Crash: a mostly-unitialized crash object
        '''
        self.crash_id = crash_id

        # a mapping containing the raw crash meta data
        self.raw_crash = {}

        # a mapping of dump name keys and paths to file system locations
        # for the dump data
        self.dumps = {} # TODO implement, see
        # socorro.external.crashstorage_base.MemoryDumpsMapping()

        # a mapping containing the processed crash meta data
        self.processed_crash = {} # TODO DotDict()

        # stores supressed errors that occur during transformation steps
        # for the lifetime of this crash object, intended to be append and
        # read only
        self._errors = []

    def transform(self, rule=Identity, supress_errors=False):
        '''applies a transformation to the internal crash state

        :arg Callable rule: callable that will perform the transformation

        :arg Boolean supress_errors: should errors be supressed and stored
        internally. Historically transformation failures have not been
        treated as fatal, and most transformations have been written assuming that failure is a normal control signal. Still, this defaults to `False` because silencing failure should be explicit.

        :raises Error: if supress_errors is False this may raise arbitrary
        errors
        '''
        try:
            rule(self.crash_id, self.raw_crash, self.dumps, self.processed_crash)
        except Exception as x:
            # TODO logging here
            if not supress_errors:
                raise
            self._errors.append(x)

        return self

    def pipeline(self, *args, supress_errors=False):
        '''sugar for applying multiple transformations

        :arg Callables *args: an arbitrary number of callable rules to
        be executed in succession

        :raises Error: if supress_errors is False this may raise arbitrary
        errors
        '''
        for arg in args:
            self.transform(arg, supress_errors=supress_errors)
        return self

    def fetch(self, supress_errors=False):
        '''fetch remote crash information, overwriting local state.

        supress_errors - Boolean should errors be supressed and stored
        internally

        :raises Error: this touches the network, so all kinds of things
        may go wrong. These errors are generally fatal and should not be
        supressed.
        '''
        self.transform(get_crash_data, supress_errors)
        return self

    def save(self, supress_errors=False):
        '''write local crash information to remote sources,
        overwriting their representation with this object's state.

        :raises Error: high seas in a rickety boat, here. Errors here are
        generally fatal and should not be supressed.
        '''
        self.transform(put_crash_data, supress_errors)
        return self

def get_crash_data(crash_id, raw_crash, dumps, processed_crash):
    """Attempt to fetch everything we know about a crash_id.

    If the raw_crash or raw_dumps cannot be found, abort.
    If the processed_crash exists, reuse that, else creat one.
    """
    # TODO: implement get_raw_crash, get_raw_dumps_as_files
    # TODO: clean this up
    return
    try:
        # socorro/external/boto/BotoCrashStorage.get_raw_crash()
        raw_crash = get_raw_crash(crash_id)
        # socorro/external/boto/BotoCrashStorage.get_raw_dumps_as_files()
        dumps = get_raw_dumps_as_files(crash_id)
        try:
            # socorro/external/boto/BotoCrashStorage.get_unredacted_processed()
            processed_crash = get_unredacted_processed(crash_id)
        except CrashIDNotFound:
            processed_crash = DotDict()
    except CrashIDNotFound:
        _reject(crash_id, 'CrashIDNotFound') # from processor2015/processor_2015.py
    except Exception:
        _reject(crash_id, 'error loading crash')
    return raw_crash, dumps, processed_crash

def put_crash_data(crash_id, raw_crash, dumps, processed_crash):
    return
    """write the modified crashes"""

    # bug 866973 - save_raw_and_processed() instead of just
    # save_processed().  The raw crash may have been modified
    # by the processor rules.  The individual crash storage
    # implementations may choose to honor re-saving the raw_crash
    # or not.

    # TODO replace this crashstorage class
    self.destination.save_raw_and_processed(
        raw_crash,
        None,
        processed_crash,
        crash_id
    )
    logger.info('saved - %s', crash_id)

def _reject(crash_id, reason):
    logger.warning("%s rejected: %s", crash_id, reason)


def transform(self, raw_crash, dumps, processed_crash):
    """business logic to modify dumps and raw crash into a final
    processed crash form"""


    if "processor_notes" in processed_crash:
        original_processor_notes = [
            x.strip() for x in processed_crash.processor_notes.split(";")
        ]
        processor_meta_data.processor_notes.append(
            "earlier processing: %s" % processed_crash.get(
                "started_datetime",
                'Unknown Date'
            )
        )
    else:
        original_processor_notes = []

    processed_crash.success = False
    processed_crash.started_datetime = utc_now()
    # for backwards compatibility:
    processed_crash.startedDateTime = processed_crash.started_datetime
    processed_crash.signature = 'EMPTY: crash failed to process'

    crash_id = raw_crash.get('uuid', 'unknown')
    try:
        # quit_check calls ought to be scattered around the code to allow
        # the processor to be responsive to requests to shut down.
        # quit_check()

        processor_meta_data.started_timestamp = self._log_job_start(
            crash_id
        )

        # apply transformations
        #    step through each of the rule sets to apply the rules.
        for a_rule_set_name, a_rule_set in self.rule_system.iteritems():
            # for each rule set, invoke the 'act' method - this method
            # will be the method specified in fourth element of the
            # rule set configuration list.
            a_rule_set.act(
                raw_crash,
                raw_dumps,
                processed_crash,
                processor_meta_data
            )
            quit_check()

        # the crash made it through the processor rules with no exceptions
        # raised, call it a success.
        processed_crash.success = True

    except Exception as x:
        self.config.logger.warning(
            'Error while processing %s: %s',
            crash_id,
            str(x),
            exc_info=True
        )
        processor_meta_data.processor_notes.append(
            'unrecoverable processor error: %s' % x
        )

    # the processor notes are in the form of a list.  Join them all
    # together to make a single string
    processor_meta_data.processor_notes.extend(original_processor_notes)
    processed_crash.processor_notes = '; '.join(
        processor_meta_data.processor_notes
    )
    completed_datetime = utc_now()
    processed_crash.completed_datetime = completed_datetime
    # for backwards compatibility:
    processed_crash.completeddatetime = completed_datetime

    self._log_job_end(
        processed_crash.success,
        crash_id
    )

    return raw_crash, dumps, processed_crash
