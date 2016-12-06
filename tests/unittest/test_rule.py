# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from everett.manager import ConfigManager
import pytest

from processor.rule import Identity, Introspector, Rule

class TestRule:

    def test_default_rule(self):
        _ = frozenset((0,))
        r = Rule()
        assert r.predicate(_, _, _, _)
        r.action(_, _, _, _)
        assert _ == frozenset((0,))
