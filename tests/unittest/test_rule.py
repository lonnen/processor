# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from processor.rule import (CreateMetadata, Identity, Introspector, Rule,
    SaveMetadata, UUIDCorrection)

# rules expect a dict-like interface for most args
from tests.testlib import _dict as _


class TestRule:

    def test_default_rule(self):
        __ = frozenset(_)
        r = Rule()
        assert r.predicate(__, __, __, __)
        r.action(__, __, __, __)
        assert __ == frozenset(_)

    def test_rule_is_callable(self):
        assert callable(Rule())

    def test_rules_throw_errors(self):
        with pytest.raises(ZeroDivisionError):
            BadTransformRule()(_, _, _, _)


class BadTransformRule(Rule):
    '''Utility subclass for testing bad behavior in the base rule class,
    not a testing class
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        raw_crash = 1 / 0


class TestIdentityRule:

    def test_happy_path(self):
        __ = 1
        r = Identity()
        r(__, __, __, __)
        assert __ == 1


class TestIntrospectorRule:

    def test_happy_path(self, loggingmock):
        __ = 1
        with loggingmock(['processor.rule']) as lm:
            r = Introspector()
            r(__, __, __, __)
            assert lm.has_record(
                name='processor.rule',
                levelname='INFO',
                msg_contains='(1, 1, 1, 1)'
            )


class TestUUIDCorrection:

    def test_happy_path(self):
        raw_crash = {}
        crash_id = 'Wilma'
        r = UUIDCorrection()
        assert r.predicate(crash_id, raw_crash, _, _)
        r.action(crash_id, raw_crash, _, _)
        assert 'uuid' in raw_crash and raw_crash['uuid'] == crash_id

class TestCreateMetadata:

    def test_no_history(self):
        processed_crash = {}
        CreateMetadata()(_, _, _, processed_crash)
        assert 'metadata' in processed_crash

    def test_with_history(self):
        processed_crash = {
            'processor_notes': 'dwight; wilma'
        }
        CreateMetadata()(_, _, _, processed_crash)
        metadata = processed_crash['metadata']
        assert 'original_processor_notes' in metadata
        assert (metadata['processor_notes'] ==
            ['earlier processing: Unknown Date'])

class TestSaveMetadata:

    def test_no_history(self):
        processed_crash = {
            'metadata': {
                'processor_notes': ['dwight', 'wilma'],
            }
        }

        assert 'processor_notes' not in processed_crash
        SaveMetadata()(_, _, _, processed_crash)
        assert 'metadata' not in processed_crash
        assert processed_crash.get('processor_notes') == 'dwight; wilma'

    def test_with_history(self):
        processed_crash = {
            'metadata': {
                'processor_notes': ['dwight', 'wilma'],
                'original_processor_notes': [
                    'Processor2015',
                    'earlier processing: Unknown Date'
                ]
            }
        }

        SaveMetadata()(_, _, _, processed_crash)
        assert 'metadata' not in processed_crash
        assert (processed_crash.get('processor_notes') ==
            'dwight; wilma; Processor2015; earlier processing: Unknown Date')
        assert processed_crash.get('completed_datetime', None) #TODO: freezegun
        assert processed_crash.get('success')
