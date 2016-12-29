# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import pytest

from processor.crash import Crash
from processor.rule import Identity, Introspector, Rule

from tests.unittest.test_rule import BadTransformRule

class TestCrash:

    def test_fetch_crash_info(self):
        crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
        assert crash.crash_id == 'AAAAAAAA-1111-4242-FFFB-094F01B8FF11'
        crash.fetch() # TODO mock this out

    def test_transform_modifies_state(self):
        crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
        pass

    def test_transform_error_suppressed(self):
        crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
        crash.transform(BadTransformRule(), supress_errors=True)
        assert len(crash._errors) == 1
        assert isinstance(crash._errors[0], ZeroDivisionError)

    def test_transform_error_unsuppressed(self):
        crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
        with pytest.raises(ZeroDivisionError):
            crash.transform(BadTransformRule())

    def test_transform_pipelining(self):
        crash = Crash('AAAAAAAA-1111-4242-FFFB-094F01B8FF11')
        crash.pipeline(
            Renamer(''),
            Introspector(),
            Renamer(''),
            Introspector()
        )

class Renamer(Rule):

    def __init__(self, new_name):
        self.new_name = new_name

    def __call__(self, crash_id, raw_crash, dumps, processed_crash):
        crash_id = self.new_name
