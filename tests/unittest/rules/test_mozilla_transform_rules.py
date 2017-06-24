# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from jansky.rules.mozilla_transform_rules import (
    AddonsRule,
    DatesAndTimesRule,
    EnvironmentRule,
    ESRVersionRewrite,
    ExploitabilityRule,
    FlashVersionRule,
    JavaProcessRule,
    PluginContentURL,
    PluginRule,
    PluginUserComment,
    ProductRewrite,
    ProductRule,
    ThemePrettyNameRule,
    TopMostFilesRule,
    UserDataRule,
    Winsock_LSPRule
)
from jansky.util import (
    datetime_from_isodate_string
)

from tests.testlib import _


class TestAddonsRule:

    def test_action_nothing_exppected(self, raw_crash, processed_crash):
        AddonsRule()(_, raw_crash, _, processed_crash)
        assert (processed_crash['addons'] == [
            ('adblockpopups@jessehakanen.net', '0.3'),
            ('dmpluginff@westbyte.com', '1,4.8'),
            ('firebug@software.joehewitt.com', '1.9.1'),
            ('killjasmin@pierros14.com', '2.4'),
            ('support@surfanonymous-free.com', '1.0'),
            ('uploader@adblockfilters.mozdev.org', '2.1'),
            ('{a0d7ccb3-214d-498b-b4aa-0e8fda9a7bf7}', '20111107'),
            ('{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}', '2.0.3'),
            ('anttoolbar@ant.com', '2.4.6.4'),
            ('{972ce4c6-7e08-4474-a285-3208198ce6fd}', '12.0'),
            ('elemhidehelper@adblockplus.org', '1.2.1')
        ])
        assert processed_crash['addons_checked']

    def test_action_colon_in_addon_version(self, raw_crash, processed_crash):
        raw_crash['Add-ons'] = 'adblockpopups@jessehakanen.net:0:3:1'
        raw_crash['EMCheckCompatibility'] = 'Nope'

        AddonsRule()(_, raw_crash, _, processed_crash)

        assert (processed_crash['addons'] == [
            ('adblockpopups@jessehakanen.net', '0:3:1'),
        ])
        assert not processed_crash['addons_checked']

    def test_action_addon_is_nonsense(self, raw_crash, processed_crash):
        raw_crash['Add-ons'] = 'naoenut813teq;mz;<[`19ntaotannn8999anxse `'

        AddonsRule()(_, raw_crash, _, processed_crash)

        assert (processed_crash['addons'] == [
            ('naoenut813teq;mz;<[`19ntaotannn8999anxse `', ''),
        ])
        assert processed_crash['addons_checked']


class TestDatesAndTimesRule:

    def test_everything_we_hoped_for(self, raw_crash, processed_crash):
        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 1336519554
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('2012-05-08 23:25:54+00:00')
        )
        assert processed_crash['install_age'] == 1079662
        assert processed_crash['uptime'] == 20116
        assert processed_crash['last_crash'] == 86985

    def test_bad_timestamp(self, raw_crash, processed_crash):
        raw_crash['timestamp'] = 'hi there'

        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 1336519554
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('2012-05-08 23:25:54+00:00')
        )
        assert processed_crash['install_age'] == 1079662
        assert processed_crash['uptime'] == 20116
        assert processed_crash['last_crash'] == 86985
        assert (
            processed_crash['metadata']['processor_notes'] ==
            ['non-integer value of "timestamp"']
        )

    def test_bad_timestamp_and_no_crash_time(self, raw_crash, processed_crash):
        raw_crash['timestamp'] = 'hi there'
        del raw_crash['CrashTime']

        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 0
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('1970-01-01 00:00:00+00:00')
        )
        assert processed_crash['install_age'] == -1335439892
        assert processed_crash['uptime'] == 0
        assert processed_crash['last_crash'] == 86985
        assert (
            processed_crash['metadata']['processor_notes'] ==
            [
                'non-integer value of "timestamp"',
                'WARNING: raw_crash missing CrashTime'
            ]
        )

    def test_no_startup_time_bad_timestamp(self, raw_crash, processed_crash):
        raw_crash['timestamp'] = 'hi there'
        del raw_crash['StartupTime']

        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 1336519554
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('2012-05-08 23:25:54+00:00')
        )
        assert processed_crash['install_age'] == 1079662
        assert processed_crash['uptime'] == 0
        assert processed_crash['last_crash'] == 86985
        assert (
            processed_crash['metadata']['processor_notes'] ==
            [
                'non-integer value of "timestamp"',
            ]
        )

    def test_no_startup_time(self, raw_crash, processed_crash):
        del raw_crash['StartupTime']

        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 1336519554
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('2012-05-08 23:25:54+00:00')
        )
        assert processed_crash['install_age'] == 1079662
        assert processed_crash['uptime'] == 0
        assert processed_crash['last_crash'] == 86985
        assert (processed_crash['metadata']['processor_notes'] == [])

    def test_bad_startup_time(self, raw_crash, processed_crash):
        raw_crash['StartupTime'] = 'feed the goats'

        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 1336519554
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('2012-05-08 23:25:54+00:00')
        )
        assert processed_crash['install_age'] == 1079662
        assert processed_crash['uptime'] == 1336519554
        assert processed_crash['last_crash'] == 86985
        assert (
            processed_crash['metadata']['processor_notes'] ==
            [
                'non-integer value of "StartupTime"',
            ]
        )

    def test_bad_install_time(self, raw_crash, processed_crash):
        raw_crash['InstallTime'] = 'feed the goats'

        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 1336519554
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('2012-05-08 23:25:54+00:00')
        )
        assert processed_crash['install_age'] == 1336519554
        assert processed_crash['uptime'] == 20116
        assert processed_crash['last_crash'] == 86985
        assert (
            processed_crash['metadata']['processor_notes'] ==
            [
                'non-integer value of "InstallTime"',
            ]
        )

    def test_bad_seconds_since_last_crash(self, raw_crash, processed_crash):
        raw_crash['SecondsSinceLastCrash'] = 'feed the goats'

        DatesAndTimesRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['submitted_timestamp'] ==
            datetime_from_isodate_string(raw_crash['submitted_timestamp'])
        )
        assert (
            processed_crash['date_processed'] ==
            processed_crash['submitted_timestamp']
        )
        assert processed_crash['crash_time'] == 1336519554
        assert (
            processed_crash['client_crash_date'] ==
            datetime_from_isodate_string('2012-05-08 23:25:54+00:00')
        )
        assert processed_crash['install_age'] == 1079662
        assert processed_crash['uptime'] == 20116
        assert processed_crash['last_crash'] is None
        assert (
            processed_crash['metadata']['processor_notes'] ==
            [
                'non-integer value of "SecondsSinceLastCrash"',
            ]
        )


class TestEnvironmentRule:

    def test_everything_we_hoped_for(self, raw_crash, processed_crash):
        EnvironmentRule()(_, raw_crash, _, processed_crash)
        assert (
            processed_crash['app_notes'] ==
            "AdapterVendorID: 0x1002, AdapterDeviceID: 0x7280, "
            "AdapterSubsysID: 01821043, "
            "AdapterDriverVersion: 8.593.100.0\nD3D10 Layers? D3D10 "
            "Layers- D3D9 Layers? D3D9 Layers- "
        )


class TestESRVersionRewrite:

    def test_everything_we_hoped_for(self, raw_crash):
        raw_crash['ReleaseChannel'] = 'esr'
        ESRVersionRewrite()(_, raw_crash, _, _)

        assert raw_crash['Version'] == '12.0esr'

    def test_wrong_crash(self, raw_crash):
        ESRVersionRewrite()(_, raw_crash, _, _)

        assert raw_crash['Version'] == '12.0'  # unchanged

    def test_this_is_really_broken(self, raw_crash):
        raw_crash['ReleaseChannel'] = 'esr'
        del raw_crash['Version']

        with pytest.raises(KeyError) as failure:
            ESRVersionRewrite()(_, raw_crash, _, _)

        assert (
            failure.value.args[0] ==
            '"Version" missing from esr release raw_crash'
        )


class TestExploitabilityRule:

    def test_everything_we_hoped_for(self, processed_crash):
        ExploitabilityRule()(_, _, _, processed_crash)

        assert processed_crash['exploitability'] == 'high'

    def test_this_is_not_the_crash(self):
        processed_crash = {
            'metadata': {
                'processor_notes': []
            }
        }

        ExploitabilityRule()(_, _, _, processed_crash)

        assert processed_crash['exploitability'] == 'unknown'


class TestFlashVersionRule:

    def test_get_flash_version(self):
        test_tuples = [
            ('NPSWF32_1_2_3.dll', '1.2.3', None, '1.2.3'),
            ('NPSWF32_1_2_3.dll', None, None, '1.2.3'),
            ('FlashPlayerPlugin_2_3_4.exe', '2.3.4', None, '2.3.4'),
            ('FlashPlayerPlugin_2_3_4.exe', None, None, '2.3.4'),
            ('libflashplayer3.4.5.so', '3.4.5', None, '3.4.5'),
            ('libflashplayer3.4.5.so', None, None, '3.4.5'),
            ('Flash Player-', '4.5.6', None, '4.5.6'),
            ('Flash Player-4.5.6', None, None, '4.5.6'),
            ('Flash Player-', '4.5.6', '83CF4DC03621B778E931FC713889E8F10',
                '4.5.6'),
            ('Flash Player-4.5.6', None,
                '83CF4DC03621B778E931FC713889E8F10', '4.5.6'),
            ('Flash Player-', None,
                '83CF4DC03621B778E931FC713889E8F10',
                '9.0.16.0')
        ]

        for params in test_tuples:
            assert (FlashVersionRule()._get_flash_version(
                filename=params[0],
                version=params[1],
                debug_id=params[2]) == params[3])

    def test_everything_we_hoped_for(self, processed_crash):
        FlashVersionRule()(_, _, _, processed_crash)

        assert processed_crash['flash_version'] == '9.1.3.08'


class TestJavaProcessRule:

    def test_everything_we_hoped_for(self, raw_crash, processed_crash):
        raw_crash['JavaStackTrace'] = "this is a Java Stack trace"

        JavaProcessRule()(_, raw_crash, _, processed_crash)

        assert 'java_stack_trace' in processed_crash
        assert (
            processed_crash['java_stack_trace'] ==
            raw_crash['JavaStackTrace']
        )

    def test_missing_stuff(self, raw_crash, processed_crash):
        # no raw_crash java stack trace

        JavaProcessRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['java_stack_trace'] is None


class TestPluginContentURL:

    def test_everything_we_hoped_for(self, raw_crash):
        raw_crash['PluginContentURL'] = 'http://mozilla.com'
        raw_crash['URL'] = 'http://google.com'
        PluginContentURL()(_, raw_crash, _, _)

        assert raw_crash['URL'] == 'http://mozilla.com'

    def test_wrong_crash(self, raw_crash):
        raw_crash['URL'] = 'http://google.com'
        PluginContentURL()(_, raw_crash, _, _)

        assert raw_crash['URL'] == 'http://google.com'  # unchanged


class TestPluginRule:

    def test_plugin_hang(self, raw_crash, processed_crash):
        raw_crash['PluginHang'] = 1
        raw_crash['Hang'] = 0
        raw_crash['ProcessType'] = 'plugin'
        raw_crash['PluginFilename'] = 'x.exe'
        raw_crash['PluginName'] = 'X'
        raw_crash['PluginVersion'] = '0.0'

        PluginRule()(_, raw_crash, _, processed_crash)

        assert (
            processed_crash['hangid'] ==
            'fake-00000000-0000-0000-0000-000002140504'
        )
        assert processed_crash['hang_type'] == -1
        assert processed_crash['process_type'] == 'plugin'
        assert processed_crash['PluginFilename'] == 'x.exe'
        assert processed_crash['PluginName'] == 'X'
        assert processed_crash['PluginVersion'] == '0.0'

    def test_browser_hang(self, raw_crash, processed_crash):
        raw_crash['Hang'] = 1
        raw_crash['ProcessType'] = 'browser'

        PluginRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['hangid'] is None
        assert processed_crash['hang_type'] == 1
        assert processed_crash['process_type'] == 'browser'
        assert 'PluginFilename' not in processed_crash
        assert 'PluginName' not in processed_crash
        assert 'PluginVersion' not in processed_crash

    def test_normal_crash(self, raw_crash, processed_crash):
        PluginRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['hangid'] is None
        assert processed_crash['hang_type'] == 0
        assert 'PluginFilename' not in processed_crash
        assert 'PluginName' not in processed_crash
        assert 'PluginVersion' not in processed_crash


class TestPluginUserComment:

    def test_everything_we_hoped_for(self, raw_crash):
        raw_crash['PluginUserComment'] = 'I hate it when this happens'
        raw_crash['Comments'] = 'I wrote something here, too'
        PluginUserComment()(_, raw_crash, _, _)

        assert raw_crash['Comments'] == 'I hate it when this happens'

    def test_wrong_crash(self, raw_crash):
        raw_crash['Comments'] = 'I wrote something here, too'
        PluginUserComment()(_, raw_crash, _, _)

        assert raw_crash['Comments'] == 'I wrote something here, too'


class TestProductRewrite:

    def test_everything_we_hoped_for(self, raw_crash):
        ProductRewrite()(_, raw_crash, _, _)

        assert raw_crash['ProductName'] == 'FennecAndroid'

    def test_wrong_crash(self, raw_crash):
        raw_crash['ProductID'] = 'arbitrary-garbage-from-the-network'
        ProductRewrite()(_, raw_crash, _, _)

        assert raw_crash['ProductName'] == 'Firefox'  # unchanged


class TestProductRule:

    def test_everything_we_hoped_for(self, raw_crash, processed_crash):
        ProductRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['product'] == 'Firefox'
        assert processed_crash['version'] == '12.0'
        assert (
            processed_crash['productid'] ==
            '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}'
        )
        assert processed_crash['distributor'] == 'Mozilla'
        assert processed_crash['distributor_version'] == '12.0'
        assert processed_crash['release_channel'] == 'release'
        assert processed_crash['build'] == '20120420145725'


class TestThemePrettyNameRule:

    def test_everything_we_hoped_for(self, processed_crash):
        processed_crash['addons'] = [
            ('adblockpopups@jessehakanen.net', '0.3'),
            ('dmpluginff@westbyte.com', '1,4.8'),
            ('firebug@software.joehewitt.com', '1.9.1'),
            ('killjasmin@pierros14.com', '2.4'),
            ('support@surfanonymous-free.com', '1.0'),
            ('uploader@adblockfilters.mozdev.org', '2.1'),
            ('{a0d7ccb3-214d-498b-b4aa-0e8fda9a7bf7}', '20111107'),
            ('{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}', '2.0.3'),
            ('anttoolbar@ant.com', '2.4.6.4'),
            ('{972ce4c6-7e08-4474-a285-3208198ce6fd}', '12.0'),
            ('elemhidehelper@adblockplus.org', '1.2.1')
        ]

        # the call to be tested
        ThemePrettyNameRule()(_, _, _, processed_crash)

        expected_addon_list = [
            ('adblockpopups@jessehakanen.net', '0.3'),
            ('dmpluginff@westbyte.com', '1,4.8'),
            ('firebug@software.joehewitt.com', '1.9.1'),
            ('killjasmin@pierros14.com', '2.4'),
            ('support@surfanonymous-free.com', '1.0'),
            ('uploader@adblockfilters.mozdev.org', '2.1'),
            ('{a0d7ccb3-214d-498b-b4aa-0e8fda9a7bf7}', '20111107'),
            ('{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}', '2.0.3'),
            ('anttoolbar@ant.com', '2.4.6.4'),
            ('{972ce4c6-7e08-4474-a285-3208198ce6fd} (default theme)',
             '12.0'),
            ('elemhidehelper@adblockplus.org', '1.2.1')
        ]
        assert processed_crash['addons'] == expected_addon_list


class TestTopMostFilesRule:

    def test_everything_we_hoped_for(self, processed_crash):
        processed_crash['json_dump'] = {
            'crash_info': {
                'crashing_thread': 0
            },
            'crashing_thread': {
                'frames': [
                    {
                        'source': 'not-the-right-file.dll'
                    },
                    {
                        'file': 'not-the-right-file.cpp'
                    },
                ]
            },
            'threads': [
                {
                    'frames': [
                        {
                            'source': 'dwight.dll'
                        },
                        {
                            'file': 'wilma.cpp'
                        },
                    ]
                },
            ]
        }

        TopMostFilesRule()(_, _, _, processed_crash)

        assert processed_crash['topmost_filenames'] == 'wilma.cpp'


class TestUserDataRule:

    def test_everything_we_hoped_for(self, raw_crash, processed_crash):
        UserDataRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['url'] == 'http://www.mozilla.com'
        assert (
            processed_crash['user_comments'] ==
            'why did my browser crash?  #fail'
        )
        assert processed_crash['email'] == 'noreply@mozilla.com'
        assert processed_crash['user_id'] == ''


class TestWinsock_LSPRule:

    def test_everything_we_hoped_for(self, raw_crash, processed_crash):
        raw_crash['Winsock_LSP'] = 'really long string'

        Winsock_LSPRule()(_, raw_crash, _, processed_crash)
        assert processed_crash['Winsock_LSP'] == 'really long string'

    def test_missing_key(self, raw_crash, processed_crash):
        del raw_crash['Winsock_LSP']

        Winsock_LSPRule()(_, raw_crash, _, processed_crash)
        assert processed_crash['Winsock_LSP'] is None
