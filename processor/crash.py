# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from rule import Identity


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
      .errors()

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
        self.errors = []

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
            rule(crash_id, raw_crash, dumps, processed_crash)
        except Exception as x:
            # TODO logging here
            if not supress_errors:
                raise
            self.errors.append()
            continue

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
    pass

def put_crash_data(crash_id, raw_crash, dumps, processed_crash):
    pass
