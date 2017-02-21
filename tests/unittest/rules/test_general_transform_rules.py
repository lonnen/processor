# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from processor.rules.general_transform_rules import (
    IdentifierRule,
)

from tests.testlib import _

class TestIdentifierRule:

    def test_everything_we_hoped_for(self, raw_crash):
        processed_crash = {}

        IdentifierRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['crash_id'] == raw_crash['uuid']
        assert processed_crash['uuid'] == raw_crash['uuid']
