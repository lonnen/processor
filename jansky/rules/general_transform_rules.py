# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from jansky.rule import Rule

logger = logging.getLogger(__name__)


class IdentifierRule(Rule):
    '''sets processed crash id values
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['crash_id'] = raw_crash['uuid']
        processed_crash['uuid'] = raw_crash['uuid']


class CPUInfoRule(Rule):
    '''lift cpu_info and count out of the dump and into top-level fields
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['cpu_info'] = ''
        processed_crash['cpu_name'] = ''
        try:
            processed_crash['cpu_info'] = (
                '%s | %s' % (
                    processed_crash['json_dump']['system_info']['cpu_info'],
                    processed_crash['json_dump']['system_info']['cpu_count']
                )
            )
        except KeyError:
            # cpu_count is likely missing
            processed_crash['cpu_info'] = (
                processed_crash['json_dump']['system_info']['cpu_info']
            )
        processed_crash['cpu_name'] = (
            processed_crash['json_dump']['system_info']['cpu_arch']
        )


class OSInfoRule(Rule):
    '''lift os_name and os_version out of the dump and into top-level fields
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['os_name'] = (
            processed_crash['json_dump']['system_info']['os'].strip()
        )
        processed_crash['os_version'] = (
            processed_crash['json_dump']['system_info']['os_ver'].strip()
        )
