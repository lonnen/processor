# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import logging
import re
import time

from sys import maxsize


from jansky.util import get_date_from_crash_id, datetime_from_isodate_string, utc_now
from jansky.rule import Rule

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
            get_date_from_crash_id(raw_crash['uuid'])
        )

        if isinstance(processed_crash['submitted_timestamp'], str):
            processed_crash['submitted_timestamp'] = datetime_from_isodate_string(
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


class FlashVersionRule(Rule):
    '''detect if flash is a module and pretty up the name

    relies on a subset of the known "debug identifiers" for flash versions,
    associated to the version and a regular expression to match Flash file
    names
    '''

    _KNOWN_FLASH_IDENTIFIERS = {
        '7224164B5918E29AF52365AF3EAF7A500': '10.1.51.66',
        'C6CDEFCDB58EFE5C6ECEF0C463C979F80': '10.1.51.66',
        '4EDBBD7016E8871A461CCABB7F1B16120': '10.1',
        'D1AAAB5D417861E6A5B835B01D3039550': '10.0.45.2',
        'EBD27FDBA9D9B3880550B2446902EC4A0': '10.0.45.2',
        '266780DB53C4AAC830AFF69306C5C0300': '10.0.42.34',
        'C4D637F2C8494896FBD4B3EF0319EBAC0': '10.0.42.34',
        'B19EE2363941C9582E040B99BB5E237A0': '10.0.32.18',
        '025105C956638D665850591768FB743D0': '10.0.32.18',
        '986682965B43DFA62E0A0DFFD7B7417F0': '10.0.23',
        '937DDCC422411E58EF6AD13710B0EF190': '10.0.23',
        '860692A215F054B7B9474B410ABEB5300': '10.0.22.87',
        '77CB5AC61C456B965D0B41361B3F6CEA0': '10.0.22.87',
        '38AEB67F6A0B43C6A341D7936603E84A0': '10.0.12.36',
        '776944FD51654CA2B59AB26A33D8F9B30': '10.0.12.36',
        '974873A0A6AD482F8F17A7C55F0A33390': '9.0.262.0',
        'B482D3DFD57C23B5754966F42D4CBCB60': '9.0.262.0',
        '0B03252A5C303973E320CAA6127441F80': '9.0.260.0',
        'AE71D92D2812430FA05238C52F7E20310': '9.0.246.0',
        '6761F4FA49B5F55833D66CAC0BBF8CB80': '9.0.246.0',
        '27CC04C9588E482A948FB5A87E22687B0': '9.0.159.0',
        '1C8715E734B31A2EACE3B0CFC1CF21EB0': '9.0.159.0',
        'F43004FFC4944F26AF228334F2CDA80B0': '9.0.151.0',
        '890664D4EF567481ACFD2A21E9D2A2420': '9.0.151.0',
        '8355DCF076564B6784C517FD0ECCB2F20': '9.0.124.0',
        '51C00B72112812428EFA8F4A37F683A80': '9.0.124.0',
        '9FA57B6DC7FF4CFE9A518442325E91CB0': '9.0.115.0',
        '03D99C42D7475B46D77E64D4D5386D6D0': '9.0.115.0',
        '0CFAF1611A3C4AA382D26424D609F00B0': '9.0.47.0',
        '0F3262B5501A34B963E5DF3F0386C9910': '9.0.47.0',
        'C5B5651B46B7612E118339D19A6E66360': '9.0.45.0',
        'BF6B3B51ACB255B38FCD8AA5AEB9F1030': '9.0.28.0',
        '83CF4DC03621B778E931FC713889E8F10': '9.0.16.0',
    }

    _FLASH_RE = re.compile(
        r'NPSWF32_?(.*)\.dll|'
        'FlashPlayerPlugin_?(.*)\.exe|'
        'libflashplayer(.*)\.(.*)|'
        'Flash ?Player-?(.*)'
    )

    def _get_flash_version(self, filename=None, version=None,
                           debug_id=None, **kwargs):
        """If (we recognize this module as Flash and figure out a version):
        Returns version; else (None or '')"""

        match = self._FLASH_RE.match(filename)
        if not match:
            return None

        if version:
            return version

        # we didn't get a version passed into us
        # try do deduce it
        groups = match.groups()
        if groups[0]:
            return groups[0].replace('_', '.')
        if groups[1]:
            return groups[1].replace('_', '.')
        if groups[2]:
            return groups[2]
        if groups[4]:
            return groups[4]
        return self._KNOWN_FLASH_IDENTIFIERS.get(
            debug_id,
            None
        )

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['flash_version'] = '[blank]'

        for a_module in processed_crash['json_dump']['modules']:
            flash_version = self._get_flash_version(**a_module)
            if flash_version:
                processed_crash['flash_version'] = flash_version
                return


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
        return ('ProductID' in raw_crash and
                raw_crash['ProductID'] in self.product_id_map)

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

        processed_crash['hang_type'] = 0  # normal crash, not a hang

        if raw_crash.get('Hang'):
            processed_crash['hang_type'] = 1  # browser hang
        elif raw_crash.get('HangID') or processed_crash.get('hangid'):
            processed_crash['hang_type'] = -1  # plugin hang

        processed_crash['process_type'] = raw_crash.get('ProcessType', None)

        if processed_crash.get('process_type') is not 'plugin':
            return

        processed_crash['PluginFilename'] = raw_crash.get('PluginFilename', '')
        processed_crash['PluginName'] = raw_crash.get('PluginName', '')
        processed_crash['PluginVersion'] = raw_crash.get('PluginVersion', '')


class ThemePrettyNameRule(Rule):
    """The Firefox theme shows up commonly in crash reports referenced by
    its internal ID. The ID is not easy to change, and is referenced by
    id in other software.

    This rule attempts to modify it to have a more identifiable name, like
    other built-in extensions.

    Must be run after the Addons Rule."""

    _CONVERSIONS = {
        "{972ce4c6-7e08-4474-a285-3208198ce6fd}":
            "{972ce4c6-7e08-4474-a285-3208198ce6fd} "
            "(default theme)",
    }

    def predicate(self, crash_id, raw_crash, dumps, processed_crash):
        '''addons is a list of tuples containing (extension, version)'''
        addons = processed_crash.get('addons', [])

        for extension, version in addons:
            if extension in self._CONVERSIONS:
                return True
        return False

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        addons = processed_crash['addons']

        for index, (extension, version) in enumerate(addons):
            if extension in self._CONVERSIONS:
                addons[index] = (self._CONVERSIONS[extension], version)
        return


class TopMostFilesRule(Rule):
    """Origninating from Bug 519703, the topmost_filenames was specified as
    singular, there would be only one.  The original programmer, in the
    source code stated "Lets build in some flex" and allowed the field to
    have more than one in a list.  However, in all the years that this existed
    it was never expanded to use more than just one.  Meanwhile, the code
    ambiguously would sometimes give this as as single value and other times
    return it as a list of one item.

    This rule does not try to reproduce that imbiguity and avoids the list
    entirely, just giving one single value.  The fact that the destination
    varible in the processed_crash is plural rather than singular is
    unfortunate."""

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['topmost_filenames'] = None

        json_dump = processed_crash['json_dump']
        try:
            crashing_thread = (
                json_dump['crash_info']['crashing_thread']
            )
            stack_frames = (
                json_dump['threads'][crashing_thread]['frames']
            )
        except KeyError as x:
            # guess we don't have frames or crashing_thread or json_dump
            # we have to give up
            processed_crash['metadata']['processor_notes'].append(
                "no 'topmost_file' name because '%s' is missing" % x
            )
            return

        for a_frame in stack_frames:
            source_filename = a_frame.get('file', None)
            if source_filename:
                processed_crash['topmost_filenames'] = source_filename
                return


class UserDataRule(Rule):
    '''copy user data from the raw crash to to the raw crash
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['url'] = raw_crash.get('URL', None)
        processed_crash['user_comments'] = raw_crash.get('Comments', None)
        processed_crash['email'] = raw_crash.get('Email', None)
        # processed_crash['user_id'] = raw_crash.get('UserID', '')
        processed_crash['user_id'] = ''


class Winsock_LSPRule(Rule):
    '''copy over winsock_lsp field if it exists
    '''

    def action(self, crash_id, raw_crash, dumps, processed_crash):
        processed_crash['Winsock_LSP'] = raw_crash.get('Winsock_LSP', None)
