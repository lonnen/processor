# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from processor.rules.mozilla_transform_rules import (
    AddonsRule,
    EnvironmentRule,
    ESRVersionRewrite,
    PluginContentURL,
    PluginRule,
    PluginUserComment,
    ProductRewrite,
    ProductRule,
    UserDataRule
)

from tests.testlib import _


class TestAddonsRule:

    def test_action_nothing_exppected(self, cannonical_raw_crash,
        cannonical_processed_crash):

        raw_crash = cannonical_raw_crash
        processed_crash = cannonical_processed_crash

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

    def test_action_colon_in_addon_version(self, cannonical_raw_crash,
        cannonical_processed_crash):

        raw_crash = cannonical_raw_crash
        processed_crash = cannonical_processed_crash

        raw_crash['Add-ons'] = 'adblockpopups@jessehakanen.net:0:3:1'
        raw_crash['EMCheckCompatibility'] = 'Nope'

        AddonsRule()(_, raw_crash, _, processed_crash)

        assert (processed_crash['addons'] == [
            ('adblockpopups@jessehakanen.net', '0:3:1'),
        ])
        assert not processed_crash['addons_checked']

    def test_action_addon_is_nonsense(self, cannonical_raw_crash,
        cannonical_processed_crash):

        raw_crash = cannonical_raw_crash
        processed_crash = cannonical_processed_crash

        raw_crash['Add-ons'] = 'naoenut813teq;mz;<[`19ntaotannn8999anxse `'

        AddonsRule()(_, raw_crash, _, processed_crash)

        assert (processed_crash['addons'] == [
            ('naoenut813teq;mz;<[`19ntaotannn8999anxse `', ''),
        ])
        assert processed_crash['addons_checked']



class TestEnvironmentRule:

    def test_everything_we_hoped_for(self, cannonical_raw_crash,
        cannonical_processed_crash):

        raw_crash = cannonical_raw_crash
        processed_crash = cannonical_processed_crash

        EnvironmentRule()(_, raw_crash, _, processed_crash)
        assert (processed_crash['app_notes'] ==
            "AdapterVendorID: 0x1002, AdapterDeviceID: 0x7280, "
            "AdapterSubsysID: 01821043, "
            "AdapterDriverVersion: 8.593.100.0\nD3D10 Layers? D3D10 "
            "Layers- D3D9 Layers? D3D9 Layers- ")


class TestESRVersionRewrite:

    def test_everything_we_hoped_for(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        raw_crash['ReleaseChannel'] = 'esr'
        ESRVersionRewrite()(_, raw_crash, _, _)

        assert raw_crash['Version'] == '12.0esr'

    def test_wrong_crash(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        ESRVersionRewrite()(_, raw_crash, _, _)

        assert raw_crash['Version'] == '12.0' # unchanged

    def test_this_is_really_broken(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        raw_crash['ReleaseChannel'] = 'esr'
        del raw_crash['Version']

        with pytest.raises(KeyError) as failure:
            ESRVersionRewrite()(_, raw_crash, _, _)

        assert (failure.value.args[0] ==
            '"Version" missing from esr release raw_crash')


class TestPluginContentURL:

    def test_everything_we_hoped_for(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        raw_crash['PluginContentURL'] = 'http://mozilla.com'
        raw_crash['URL'] = 'http://google.com'
        PluginContentURL()(_, raw_crash, _, _)

        assert raw_crash['URL'] == 'http://mozilla.com'

    def test_wrong_crash(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        raw_crash['URL'] = 'http://google.com'
        PluginContentURL()(_, raw_crash, _, _)

        assert raw_crash['URL'] == 'http://google.com' # unchanged


class TestPluginRule:

    def test_plugin_hang(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash

        raw_crash['PluginHang'] = 1
        raw_crash['Hang'] = 0
        raw_crash['ProcessType'] = 'plugin'
        raw_crash['PluginFilename'] = 'x.exe'
        raw_crash['PluginName'] = 'X'
        raw_crash['PluginVersion'] = '0.0'

        processed_crash = {}

        PluginRule()(_, raw_crash, _, processed_crash)

        assert (processed_crash['hangid'] ==
            'fake-00000000-0000-0000-0000-000002140504')
        assert processed_crash['hang_type'] == -1
        assert processed_crash['process_type'] == 'plugin'
        assert processed_crash['PluginFilename'] == 'x.exe'
        assert processed_crash['PluginName'] == 'X'
        assert processed_crash['PluginVersion'] == '0.0'



    def test_browser_hang(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash

        raw_crash['Hang'] = 1
        raw_crash['ProcessType'] = 'browser'

        processed_crash = {}

        PluginRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['hangid'] == None
        assert processed_crash['hang_type'] == 1
        assert processed_crash['process_type'] == 'browser'
        assert 'PluginFilename' not in processed_crash
        assert 'PluginName' not in processed_crash
        assert 'PluginVersion' not in processed_crash


    def test_normal_crash(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash

        processed_crash = {}

        PluginRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['hangid'] == None
        assert processed_crash['hang_type'] == 0
        assert 'PluginFilename' not in processed_crash
        assert 'PluginName' not in processed_crash
        assert 'PluginVersion' not in processed_crash


class TestPluginUserComment:

    def test_everything_we_hoped_for(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        raw_crash['PluginUserComment'] = 'I hate it when this happens'
        raw_crash['Comments'] = 'I wrote something here, too'
        PluginUserComment()(_, raw_crash, _, _)

        assert raw_crash['Comments'] == 'I hate it when this happens'

    def test_wrong_crash(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        raw_crash['Comments'] = 'I wrote something here, too'
        PluginUserComment()(_, raw_crash, _, _)

        assert raw_crash['Comments'] == 'I wrote something here, too'


class TestProductRewrite:

    def test_everything_we_hoped_for(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        ProductRewrite()(_, raw_crash, _, _)

        assert raw_crash['ProductName'] == 'FennecAndroid'

    def test_wrong_crash(self, cannonical_raw_crash):
        raw_crash = cannonical_raw_crash
        raw_crash['ProductID'] = 'arbitrary-garbage-from-the-network'
        ProductRewrite()(_, raw_crash, _, _)

        assert raw_crash['ProductName'] == 'Firefox' # unchanged


class TestProductRule:

    def test_everything_we_hoped_for(self, cannonical_raw_crash,
        cannonical_processed_crash):

        raw_crash = cannonical_raw_crash
        processed_crash = cannonical_processed_crash

        ProductRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['product'] == 'Firefox'
        assert processed_crash['version'] == '12.0'
        assert (processed_crash['productid'] ==
            '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}')
        assert processed_crash['distributor'] == 'Mozilla'
        assert processed_crash['distributor_version'] == '12.0'
        assert processed_crash['release_channel'] == 'release'
        assert processed_crash['build'] == '20120420145725'

class TestUserDataRule:

    def test_everything_we_hoped_for(self, cannonical_raw_crash,
        cannonical_processed_crash):

        raw_crash = cannonical_raw_crash
        processed_crash = cannonical_processed_crash

        UserDataRule()(_, raw_crash, _, processed_crash)

        assert processed_crash['url'] == 'http://www.mozilla.com'
        assert (processed_crash['user_comments'] ==
            'why did my browser crash?  #fail')
        assert processed_crash['email'] == 'noreply@mozilla.com'
        assert processed_crash['user_id'] == ''
