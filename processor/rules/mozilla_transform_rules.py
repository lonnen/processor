# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import logging
import time

from sys import maxsize


from processor.util import dateFromOoid, datetimeFromISOdateString, utc_now
from processor.rule import Rule

from urllib.parse import unquote_plus

import isodate


logger = logging.getLogger(__name__)

UTC = isodate.UTC


# TODO: rules to transform a raw crash into a processed crash
#
# s.p.mozilla_transform_rules.OutOfMemoryBinaryRule


class AddonsRule(Rule):
    '''transform add-on information into a useful form
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        addons_checked = raw_crash.get('EMCheckCompatibility', '')
        processed_crash['addons_checked'] = (addons_checked.lower() == 'true')

        if processed_crash['addons_checked']:
            addons_checked_txt = raw_crash['EMCheckCompatibility'].lower()

        original_addon_str = raw_crash.get('Add-ons')
        if not original_addon_str:
            logger.debug('AddonsRule: no addons')
            processed_crash['addons'] = []
            return

        addons = []
        for addon_pair in original_addon_str.split(','):
            addon_splits = addon_pair.split(':', 1)
            if len(addon_splits) == 1:
                processed_crash['metadata']['processor_notes'].append(
                    'add-on "%s" is a bad name and/or version' %
                    addon_pair
                )
                addon_splits.append('')
            addons.append(tuple(unquote_plus(x) for x in addon_splits))

        processed_crash['addons'] = addons


class DatesAndTimesRule(Rule):
    '''
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processor_notes = processed_crash['metadata']['processor_notes']

        processed_crash['submitted_timestamp'] = raw_crash.get(
            'submitted_timestamp',
            dateFromOoid(raw_crash['uuid'])
        )

        if isinstance(processed_crash['submitted_timestamp'], str):
            processed_crash['submitted_timestamp'] = datetimeFromISOdateString(
                processed_crash['submitted_timestamp']
            )

        processed_crash['date_processed'] = processed_crash['submitted_timestamp']

        # defaultCrashTime: must have crashed before date processed
        submitted_timestamp_as_epoch = int(
            time.mktime(processed_crash['submitted_timestamp'].timetuple())
        )

        try:
            timestampTime = int(
                raw_crash.get('timestamp', submitted_timestamp_as_epoch)
            )  # the old name for crash time
        except ValueError:
            timestampTime = 0
            processor_notes.append('non-integer value of "timestamp"')

        try:
            crash_time = int(raw_crash['CrashTime'][:10])
        except (KeyError, AttributeError):
            processor_notes.append(
                "WARNING: raw_crash missing %s" % 'CrashTime')
            crash_time = timestampTime
        except TypeError as x:
            processor_notes.append(
                ("WARNING: raw_crash['CrashTime'] contains unexpected value: ",
                    "%s; %s" % (raw_crash['CrashTime'], str(x)))
            )
            crash_time = timestampTime
        except ValueError:
            processor_notes.append(
                'non-integer value of "CrashTime" (%s)' % raw_crash.CrashTime
            )
            crash_time = 0

        processed_crash['crash_time'] = crash_time
        if crash_time == submitted_timestamp_as_epoch:
            processor_notes.append("client_crash_date is unknown")

        # StartupTime: must have started up some time before crash
        try:
            startupTime = int(raw_crash.get('StartupTime', crash_time))
        except ValueError:
            startupTime = 0
            processor_notes.append('non-integer value of "StartupTime"')

        # InstallTime: must have installed some time before startup
        try:
            installTime = int(raw_crash.get('InstallTime', startupTime))
        except ValueError:
            installTime = 0
            processor_notes.append('non-integer value of "InstallTime"')

        processed_crash['client_crash_date'] = datetime.datetime.fromtimestamp(
            crash_time,
            UTC
        )

        processed_crash['install_age'] = crash_time - installTime
        processed_crash['uptime'] = max(0, crash_time - startupTime)

        try:
            last_crash = int(raw_crash['SecondsSinceLastCrash'])
        except (KeyError, TypeError, ValueError):
            last_crash = None
            processor_notes.append(
                'non-integer value of "SecondsSinceLastCrash"'
            )

        if last_crash is not None and last_crash > maxsize:
            last_crash = None
            processor_notes.append(
                '"SecondsSinceLastCrash" larger than MAXINT - set to NULL'
            )
        processed_crash['last_crash'] = last_crash

        return True


class EnvironmentRule(Rule):
    '''move the Notes from the raw_crash to the processed crash
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['app_notes'] = raw_crash.get('Notes', '')


class ESRVersionRewrite(Rule):
    '''rewrites the version to denote esr builds where appropriate
    '''

    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        return raw_crash.get('ReleaseChannel', '') == 'esr'

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        try:
            raw_crash['Version'] += 'esr'
        except KeyError:
            raise KeyError(
                '"Version" missing from esr release raw_crash')


class ExploitablityRule(Rule):
    '''lifts exploitability out of the dump and into top-level fields
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        try:
            processed_crash['exploitability'] = (
                processed_crash['json_dump']
                ['sensitive']['exploitability']
            )
        except KeyError:
            processed_crash['exploitability'] = 'unknown'
            processed_crash['metadata']['processor_notes'].append(
                "exploitability information missing"
            )


class FennecBetaError20150430(Rule):
    '''Correct the release channel for Fennec build 20150427090529
    '''

    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        return (raw_crash['ProductName'].startswith('Fennec') and
            raw_crash['BuildID'] == '20150427090529' and
            raw_crash['ReleaseChannel'] == 'release')

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        raw_crash['ReleaseChannel'] = 'beta'
        return True


class JavaProcessRule(Rule):
    '''copy or initialize the java_stack_trace
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['java_stack_trace'] = raw_crash.setdefault(
            'JavaStackTrace',
            None
        )


class PluginContentURL(Rule):
    '''overwrite 'URL' with 'PluginContentURL' if it exists
    '''

    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        return 'PluginContentURL' in raw_crash

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        raw_crash['URL'] = raw_crash['PluginContentURL']


class PluginUserComment(Rule):
    '''replace the top level 'Comment' with 'PluginUserComment' if it exists
    '''

    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        return 'PluginUserComment' in raw_crash

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        raw_crash['Comments'] = raw_crash['PluginUserComment']


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


class ProductRewrite(Rule):
    '''map a raw_crash ProductID to a ProductName using a lookup table
    '''

    def __init__(self):
        super(ProductRewrite, self).__init__()
        self.product_id_map = {
            # TODO: this is pulled from the database in processor2015
            # TODO: figure out what to do here instead, mocking for now
            # in processor2015 the value was a complex object built from a
            # sql table:
            #   'productid', 'product_name', 'rewrite'
            # simplified here, if we shouldn't rewrite it shouldn't be in
            # this lookup table
            '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}': 'FennecAndroid',
            '{ec8030f7-c20a-464f-9b0e-13b3a9e97384}': 'Chrome',
            '{ec8030f7-c20a-464f-9b0e-13c3a9e97384}': 'Safari',
        }

    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        return ('ProductID' in raw_crash
            and raw_crash['ProductID'] in self.product_id_map)

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        product_id = raw_crash['ProductID']
        old_product_name = raw_crash['ProductName']
        new_product_name = self.product_id_map[product_id]

        raw_crash['ProductName'] = new_product_name

        logger.debug(
            'product name changed from %s to %s based '
            'on productID %s',
            old_product_name,
            new_product_name,
            product_id
        )


class PluginRule(Rule):
    '''Detects and notes hangs, sometimes hangs in in plugins
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['hangid'] = raw_crash.get('HangID', None)

        if raw_crash.get('PluginHang', False):
            processed_crash['hangid'] = 'fake-' + raw_crash['uuid']


        processed_crash['hang_type'] = 0 # normal crash, not a hang

        if raw_crash.get('Hang'):
            processed_crash['hang_type'] = 1 # browser hang
        elif raw_crash.get('HangID') or processed_crash.get('hangid'):
            processed_crash['hang_type'] = -1 # plugin hang

        processed_crash['process_type'] = raw_crash.get('ProcessType', None)

        if processed_crash.get('process_type') is not 'plugin':
            return

        processed_crash['PluginFilename'] = raw_crash.get('PluginFilename', '')
        processed_crash['PluginName'] = raw_crash.get('PluginName', '')
        processed_crash['PluginVersion'] = raw_crash.get('PluginVersion', '')


class UserDataRule(Rule):
    '''copy user data from the raw crash to to the raw crash
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['url'] = raw_crash.get('URL', None)
        processed_crash['user_comments'] = raw_crash.get('Comments', None)
        processed_crash['email'] = raw_crash.get('Email', None)
        #processed_crash['user_id'] = raw_crash.get('UserID', '')
        processed_crash['user_id'] = ''


class Winsock_LSPRule(Rule):
    '''copy over winsock_lsp field if it exists
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['Winsock_LSP'] = raw_crash.get('Winsock_LSP', None)
