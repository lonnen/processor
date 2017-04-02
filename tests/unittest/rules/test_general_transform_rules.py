# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from processor.rules.general_transform_rules import (
    CPUInfoRule,
    IdentifierRule,
    OSInfoRule
)

from tests.testlib import _

class TestIdentifierRule:

    def test_everything_we_hoped_for(self, raw_crash):
        processed_crash = {}

        IdentifierRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['crash_id'] == raw_crash['uuid']
        assert processed_crash['uuid'] == raw_crash['uuid']


class TestCPUInfoRule:

    def test_everything_we_hoped_for(self, processed_crash):
        CPUInfoRule()(_, _, _, processed_crash)

        assert (processed_crash['cpu_info'] ==
            "GenuineIntel family 6 model 42 stepping 7 | 4")
        assert processed_crash['cpu_name'] == "x86"

    def test_stuff_missing(self, processed_crash):
        del processed_crash['json_dump']['system_info']['cpu_count']

        CPUInfoRule()(_, _, _, processed_crash)

        assert (processed_crash['cpu_info'] ==
            "GenuineIntel family 6 model 42 stepping 7")
        assert processed_crash['cpu_name'] == "x86"


class TestOSInfoRule:

    def test_everything_we_hoped_for(self, processed_crash):
        OSInfoRule()(_, _, _, processed_crash)

        assert processed_crash['os_name'] == "Windows NT"
        assert processed_crash['os_version'] == "6.1.7601 Service Pack 1"
