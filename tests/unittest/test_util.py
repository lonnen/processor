# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime

from freezegun import freeze_time
import isodate
import pytest
import re

from jansky.util import (
    create_crash_id,
    datestring_to_weekly_partition,
    date_to_string,
    datetime_from_isodate_string,
    get_date_from_crash_id,
    string_to_datetime,
    utc_now
)

UTC = isodate.UTC


def test_utc_now():
    """Test utc_now()
    """
    res = utc_now()
    assert res.strftime('%Z') == 'UTC'
    assert res.strftime('%z') == '+0000'
    assert res.tzinfo


@freeze_time('2011-09-06 00:00:00', tz_offset=0)
def test_crash_id():
    """Tests creating crash ids"""
    crash_id = create_crash_id()

    assert get_date_from_crash_id(crash_id) == '20110906'
    assert get_date_from_crash_id(crash_id, as_datetime=True).strftime('%Y%m%d') == '20110906'


def test_crash_id_with_date():
    """Tests creating a crash id with a timestamp"""
    crash_id = create_crash_id(datetime.datetime(2016, 10, 4))

    assert get_date_from_crash_id(crash_id) == '20161004'


def test_string_to_datetime():
    """Test string_to_datetime()
    """
    # Empty date
    date = ""
    try:
        res = string_to_datetime(date)
        raise AssertionError("expect this to raise ValueError")
    except ValueError:
        pass

    # already a date
    date = datetime.datetime.utcnow()
    res = string_to_datetime(date)

    assert res == date.replace(tzinfo=UTC)
    assert res.strftime('%Z') == 'UTC'
    assert res.strftime('%z') == '+0000'

    # YY-mm-dd date
    date = "2001-11-03"
    res = string_to_datetime(date)
    assert res == datetime.datetime(2001, 11, 3, tzinfo=UTC)
    assert res.strftime('%Z') == 'UTC'  # timezone aware

    # and naughty YY-m-d date
    date = "2001-1-3"
    res = string_to_datetime(date)
    assert res == datetime.datetime(2001, 1, 3, tzinfo=UTC)
    assert res.strftime('%Z') == 'UTC'  # timezone aware

    # YY-mm-dd HH:ii:ss.S date
    date = "2001-11-30 12:34:56.123456"
    res = string_to_datetime(date)
    assert (res == datetime.datetime(2001, 11, 30, 12, 34, 56, 123456,
        tzinfo=UTC))

    # Separated date
    date = ["2001-11-30", "12:34:56"]
    res = string_to_datetime(date)
    assert res == datetime.datetime(2001, 11, 30, 12, 34, 56, tzinfo=UTC)

    # Invalid date
    date = "2001-11-32"
    try:
        res = string_to_datetime(date)
        raise AssertionError("should have raise a ValueError")
    except ValueError:
        pass


def test_string_datetime_with_timezone():
    date = "2001-11-30T12:34:56Z"
    res = string_to_datetime(date)
    assert res == datetime.datetime(2001, 11, 30, 12, 34, 56, tzinfo=UTC)
    assert res.strftime('%H') == '12'
    # because it's a timezone aware datetime
    assert res.tzname()
    assert res.strftime('%Z') == 'UTC'
    assert res.strftime('%z') == '+0000'

    # plus 3 hours east of Zulu means minus 3 hours on UTC
    date = "2001-11-30T12:10:56+03:00"
    res = string_to_datetime(date)
    expected = datetime.datetime(2001, 11, 30, 12 - 3, 10, 56, tzinfo=UTC)
    assert res == expected

    # similar example
    date = "2001-11-30T12:10:56-01:30"
    res = string_to_datetime(date)
    assert (res == datetime.datetime(2001, 11, 30, 12 + 1, 10 + 30, 56,
        tzinfo=UTC))

    # YY-mm-dd+HH:ii:ss.S date
    date = "2001-11-30 12:34:56.123456Z"
    res = string_to_datetime(date)
    assert (res == datetime.datetime(2001, 11, 30, 12, 34, 56, 123456,
        tzinfo=UTC))

    docstring = """
        * 2012-01-10T12:13:14
        * 2012-01-10T12:13:14.98765
        * 2012-01-10T12:13:14.98765+03:00
        * 2012-01-10T12:13:14.98765Z
        * 2012-01-10 12:13:14
        * 2012-01-10 12:13:14.98765
        * 2012-01-10 12:13:14.98765+03:00
        * 2012-01-10 12:13:14.98765Z
    """.strip().splitlines()
    examples = [x.replace('*', '').strip() for x in docstring]
    for example in examples:
        res = string_to_datetime(example)
        assert res.tzinfo
        assert isinstance(res, datetime.datetime)


def test_date_to_string():
    # Datetime with timezone
    date = datetime.datetime(2012, 1, 3, 12, 23, 34, tzinfo=UTC)
    res_exp = '2012-01-03T12:23:34+00:00'
    res = date_to_string(date)
    assert res == res_exp

    # Datetime without timezone
    date = datetime.datetime(2012, 1, 3, 12, 23, 34)
    res_exp = '2012-01-03T12:23:34'
    res = date_to_string(date)
    assert res == res_exp

    # Date (no time, no timezone)
    date = datetime.date(2012, 1, 3)
    res_exp = '2012-01-03'
    res = date_to_string(date)
    assert res == res_exp


def test_date_to_string_fail():
    with pytest.raises(TypeError):
        date_to_string('2012-01-03')


def test_date_to_weekly_partition_with_string():
    datestring = '2015-01-09'
    partition_exp = '20150105'

    partition = datestring_to_weekly_partition(datestring)
    assert partition == partition_exp

    # Is there a better way of testing that we handle 'now' as a date value?
    datestring = 'now'
    date_now = datetime.datetime.now().date()
    partition_exp = (date_now + datetime.timedelta(0 - date_now.weekday())).strftime('%Y%m%d')
    partition = datestring_to_weekly_partition(datestring)
    assert partition == partition_exp


def test_date_to_weekly_partition_with_datetime():
    proposed_and_expected = (
        (datetime.datetime(2014, 12, 29), '20141229'),
        (datetime.datetime(2014, 12, 30), '20141229'),
        (datetime.datetime(2014, 12, 31), '20141229'),
        (datetime.datetime(2015,  1,  1), '20141229'),
        (datetime.datetime(2015,  1,  2), '20141229'),
        (datetime.datetime(2015,  1,  3), '20141229'),
        (datetime.datetime(2015,  1,  4), '20141229'),
        (datetime.datetime(2015,  1,  5), '20150105'),
        (datetime.datetime(2015,  1,  6), '20150105'),
        (datetime.datetime(2015,  1,  7), '20150105'),
        (datetime.datetime(2015,  1,  8), '20150105'),
        (datetime.datetime(2015,  1,  9), '20150105'),
    )
    for to_be_tested, expected in proposed_and_expected:
        result = datestring_to_weekly_partition(to_be_tested)
        assert result == expected
