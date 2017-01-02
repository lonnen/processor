# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from processor.util import utc_now
from processor.rule import Rule

import logging

logger = logging.getLogger(__name__)


class IdentifierRule(Rule):
    '''sets processed crash id values
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['crash_id'] = raw_crash['uuid']
        processed_crash['uuid'] = raw_crash['uuid']
