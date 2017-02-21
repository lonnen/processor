# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import contextlib
from pathlib import Path

import sys
from unittest import mock

from everett.manager import ConfigManager
import pytest


# Add repository root so we can import Processor.
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Add testlib so we can import testlib modules.
sys.path.insert(0, str(REPO_ROOT / 'tests'))

from processor.app import setup_logging # noqa
from testlib.loggingmock import LoggingMock  # noqa


def pytest_runtest_setup():
    # Make sure we set up logging to sane default values.
    setup_logging('DEBUG')


@pytest.fixture
def randommock():
    """Returns a contextmanager that mocks random.random() at a specific value

    Usage::

        def test_something(randommock):
            with randommock(0.55):
                # test stuff...

    """
    @contextlib.contextmanager
    def _randommock(value):
        with mock.patch('random.random') as mock_random:
            mock_random.return_value = value
            yield

    return _randommock

@pytest.fixture
def loggingmock():
    """Returns a loggingmock that builds a logging mock context to record logged records

    Usage::

        def test_something(loggingmock):
            with loggingmock() as lm:
                # do stuff
                assert lm.has_record(
                    name='foo.bar',
                    level=logging.INFO,
                    msg_contains='some substring'
                )


    You can specify names, too::

        def test_something(loggingmock):
            with loggingmock(['antenna', 'botocore']) as lm:
                # do stuff
                assert lm.has_record(
                    name='foo.bar',
                    level=logging.INFO,
                    msg_contains='some substring'
                )

    """
    @contextlib.contextmanager
    def _loggingmock(names=None):
        with LoggingMock(names=names) as loggingmock:
            yield loggingmock
    return _loggingmock

@pytest.fixture
def cannonical_raw_crash():
    return {
        "uuid": '00000000-0000-0000-0000-000002140504',
        "InstallTime": "1335439892",
        "AdapterVendorID": "0x1002",
        "TotalVirtualMemory": "4294836224",
        "Comments": "why did my browser crash?  #fail",
        "Theme": "classic/1.0",
        "Version": "12.0",
        "Email": "noreply@mozilla.com",
        "Vendor": "Mozilla",
        "EMCheckCompatibility": "true",
        "Throttleable": "1",
        "id": "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}",
        "buildid": "20120420145725",
        "AvailablePageFile": "10641510400",
        "version": "12.0",
        "AdapterDeviceID": "0x7280",
        "ReleaseChannel": "release",
        "submitted_timestamp": "2012-05-08T23:26:33.454482+00:00",
        "URL": "http://www.mozilla.com",
        "timestamp": 1336519593.454627,
        "Notes": "AdapterVendorID: 0x1002, AdapterDeviceID: 0x7280, "
                 "AdapterSubsysID: 01821043, "
                 "AdapterDriverVersion: 8.593.100.0\nD3D10 Layers? D3D10 "
                 "Layers- D3D9 Layers? D3D9 Layers- ",
        "CrashTime": "1336519554",
        "Winsock_LSP": "MSAFD Tcpip [TCP/IPv6] : 2 : 1 :  \n "
                       "MSAFD Tcpip [UDP/IPv6] : 2 : 2 : "
                       "%SystemRoot%\\system32\\mswsock.dll \n "
                       "MSAFD Tcpip [RAW/IPv6] : 2 : 3 :  \n "
                       "MSAFD Tcpip [TCP/IP] : 2 : 1 : "
                       "%SystemRoot%\\system32\\mswsock.dll \n "
                       "MSAFD Tcpip [UDP/IP] : 2 : 2 :  \n "
                       "MSAFD Tcpip [RAW/IP] : 2 : 3 : "
                       "%SystemRoot%\\system32\\mswsock.dll \n "
                       "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a "
                       "\u0443\u0441\u043b\u0443\u0433 RSVP TCPv6 : 2 : 1 :  \n "
                       "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a "
                       "\u0443\u0441\u043b\u0443\u0433 RSVP TCP : 2 : 1 : "
                       "%SystemRoot%\\system32\\mswsock.dll \n "
                       "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a "
                       "\u0443\u0441\u043b\u0443\u0433 RSVP UDPv6 : 2 : 2 :  \n "
                       "\u041f\u043e\u0441\u0442\u0430\u0432\u0449\u0438\u043a "
                       "\u0443\u0441\u043b\u0443\u0433 RSVP UDP : 2 : 2 : "
                       "%SystemRoot%\\system32\\mswsock.dll",
        "FramePoisonBase": "00000000f0de0000",
        "AvailablePhysicalMemory": "2227773440",
        "FramePoisonSize": "65536",
        "StartupTime": "1336499438",
        "Add-ons": "adblockpopups@jessehakanen.net:0.3,"
                   "dmpluginff%40westbyte.com:1%2C4.8,"
                   "firebug@software.joehewitt.com:1.9.1,"
                   "killjasmin@pierros14.com:2.4,"
                   "support@surfanonymous-free.com:1.0,"
                   "uploader@adblockfilters.mozdev.org:2.1,"
                   "{a0d7ccb3-214d-498b-b4aa-0e8fda9a7bf7}:20111107,"
                   "{d10d0bf8-f5b5-c8b4-a8b2-2b9879e08c5d}:2.0.3,"
                   "anttoolbar@ant.com:2.4.6.4,"
                   "{972ce4c6-7e08-4474-a285-3208198ce6fd}:12.0,"
                   "elemhidehelper@adblockplus.org:1.2.1",
        "BuildID": "20120420145725",
        "SecondsSinceLastCrash": "86985",
        "ProductName": "Firefox",
        "legacy_processing": 0,
        "AvailableVirtualMemory": "3812708352",
        "SystemMemoryUsePercentage": "48",
        "ProductID": "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}",
        "Distributor": "Mozilla",
        "Distributor_version": "12.0",
    }

@pytest.fixture
def cannonical_processed_crash():
    return {
        'metadata': {
            'processor_notes': []
        },
        'json_dump': {
            'sensitive': {
                'exploitability': 'high'
            },
            'modules': [
                {
                    "end_addr": "0x12e6000",
                    "filename": "plugin-container.exe",
                    "version": "26.0.0.5084",
                    "debug_id": "8385BD80FD534F6E80CF65811735A7472",
                    "debug_file": "plugin-container.pdb",
                    "base_addr": "0x12e0000"
                },
                {
                    "end_addr": "0x12e6000",
                    "filename": "plugin-container.exe",
                    "version": "26.0.0.5084",
                    "debug_id": "8385BD80FD534F6E80CF65811735A7472",
                    "debug_file": "plugin-container.pdb",
                    "base_addr": "0x12e0000"
                },
                {
                    "end_addr": "0x12e6000",
                    "filename": "FlashPlayerPlugin9_1_3_08.exe",
                    "debug_id": "8385BD80FD534F6E80CF65811735A7472",
                    "debug_file": "plugin-container.pdb",
                    "base_addr": "0x12e0000"
                },
                {
                    "end_addr": "0x12e6000",
                    "filename": "plugin-container.exe",
                    "version": "26.0.0.5084",
                    "debug_id": "8385BD80FD534F6E80CF65811735A7472",
                    "debug_file": "plugin-container.pdb",
                    "base_addr": "0x12e0000"
                },
            ]
        }
    }
