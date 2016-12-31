# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from processor.util import utc_now
from processor.rule import Rule

import logging

logger = logging.getLogger(__name__)

# rules to change the internals of the raw crash
#
# s.p.mozilla_transform_rules.ProductRewrite
# s.p.mozilla_transform_rules.ESRVersionRewrite
# s.p.mozilla_transform_rules.PluginContentURL
# s.p.mozilla_transform_rules.PluginUserComment
# s.p.mozilla_transform_rules.FennecBetaError20150430


class ProductRule(Rule):
    '''transfers Product-related properties from the raw to the processed_crash,
    filling in with empty defaults where it
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['product'] = raw_crash.get('ProductName', '')
        processed_crash['version'] = raw_crash.get('Version', '')
        processed_crash['productid'] = raw_crash.get('ProductID', '')
        processed_crash['distributor'] = raw_crash.get('Distributor', None)
        processed_crash['distributor_version'] = raw_crash.get(
            'Distributor_version',
            None
        )
        processed_crash['release_channel'] = raw_crash.get('ReleaseChannel', '')
        # redundant, but I want to exactly match old processors.
        processed_crash['ReleaseChannel'] = raw_crash.get('ReleaseChannel', '')
        processed_crash['build'] = raw_crash.get('BuildID', '')
