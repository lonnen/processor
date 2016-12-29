# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from tests.testlib import _
import pytest

from processor.rule import Identity, Introspector, Rule, UUIDCorrection

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
