# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from everett.manager import ConfigManager
import pytest

from processor.rule_engine import Rule, RuleEngine, mozilla_rules

class AddProductRule(Rule):
    """Sets a product in the processed_crash iff needed"""

    def _predicate(self, raw_crash, dumps, processed_crash):
        return 'product' not in processed_crash

    def _action(self, raw_crash, dumps, processed_crash):
        product = raw_crash.get('product', 'WaterWolf')
        processed_crash['product'] = product
        return True


class TestRule:

    def test_default_rule(self):
        crash = {}
        r = Rule()
        assert r.predicate({})
        assert r.action({})

    def test_add_product_rule(self):
        raw_crash = {
          'product': 'CloudCat'
        }
        processed_crash = {}
        apr = AddProductRule()
        assert apr.predicate(raw_crash, '', processed_crash)
        assert apr.action(raw_crash, '', processed_crash)

        # asserts that product is now in the processed_crash
        assert not apr.predicate(raw_crash, '', processed_crash)
