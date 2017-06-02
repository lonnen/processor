# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import re
import uuid

import isodate


UTC = isodate.UTC


defaultDepth = 2
oldHardDepth = 4


def create_crash_id(timestamp=None, throttle_result=1):
    """Generates a crash id

    Crash ids have the following format::

        de1bb258-cbbf-4589-a673-34f800160918
                                     ^^^^^^^
                                     ||____|
                                     |  yymmdd
                                     |
                                     throttle_result

    The ``throttle_result`` should be either 0 (accept) or 1 (defer).

    :arg date/datetime timestamp: a datetime or date to use in the crash id
    :arg int throttle_result: the throttle result to encode; defaults to 1
        which is DEFER

    :returns: crash id as str

    """
    if timestamp is None:
        timestamp = utc_now().date()

    id_ = str(uuid.uuid4())
    return "%s%d%02d%02d%02d" % (
        id_[:-7], throttle_result, timestamp.year % 100, timestamp.month, timestamp.day
    )


def get_throttle_from_crash_id(crash_id):
    """Retrieve the throttle instruction from the crash_id

    :arg str crash_id: the crash id

    :returns: int

    """
    return int(crash_id[-7])


def get_date_from_crash_id(crash_id, as_datetime=False, century='20'):
    """Retrieves the date from the crash id

    :arg str crash_id: the crash id
    :arg bool as_datetime: whether or not to return a datetime; defaults to False
        which means this returns a string
    :arg str century: the century as a string

    :returns: string or datetime depending on ``as_datetime`` value

    """
    s = century + crash_id[-6:]
    if as_datetime:
        return datetime.datetime(int(s[:4]), int(s[4:6]), int(s[6:8]), tzinfo=UTC)
    return s


def date_to_string(date):
    """Transform a date or datetime object into a string and return it.

    Examples:

    >>> date_to_string(datetime.datetime(2012, 1, 3, 12, 23, 34, tzinfo=UTC))
    '2012-01-03T12:23:34+00:00'
    >>> date_to_string(datetime.datetime(2012, 1, 3, 12, 23, 34))
    '2012-01-03T12:23:34'
    >>> date_to_string(datetime.date(2012, 1, 3))
    '2012-01-03'

    """
    if isinstance(date, datetime.datetime):
        # Create an ISO 8601 datetime string
        date_str = date.strftime('%Y-%m-%dT%H:%M:%S')
        tzstr = date.strftime('%z')
        if tzstr:
            # Yes, this is ugly. And no, I haven't found a better way to have a
            # truly ISO 8601 datetime with timezone in Python.
            date_str = '%s%s:%s' % (date_str, tzstr[0:3], tzstr[3:5])
    elif isinstance(date, datetime.date):
        # Create an ISO 8601 date string
        date_str = date.strftime('%Y-%m-%d')
    else:
        raise TypeError('Argument is not a date or datetime. ')

    return date_str


def datetime_from_isodate_string(s):
    """Take an ISO date string of the form YYYY-MM-DDTHH:MM:SS.S and convert it
    into an instance of datetime.datetime

    """
    return string_to_datetime(s)


def datestring_to_weekly_partition(date_str):
    """Return a string representing a weekly partition from a date.

    Our partitions start on Mondays.

    Example::

        date = '2015-01-09'
        weekly_partition = '2014-01-05'

    """

    if isinstance(date_str, datetime.datetime):
        d = date_str
    elif date_str == 'now':
        d = datetime.datetime.now().date()
    else:
        d = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

    last_monday = d + datetime.timedelta(0 - d.weekday())

    return last_monday.strftime('%Y%m%d')


def string_to_datetime(date):
    """Return a datetime.datetime instance with tzinfo.
    I.e. a timezone aware datetime instance.

    Acceptable formats for input are:

    * 2012-01-10T12:13:14
    * 2012-01-10T12:13:14.98765
    * 2012-01-10T12:13:14.98765+03:00
    * 2012-01-10T12:13:14.98765Z
    * 2012-01-10 12:13:14
    * 2012-01-10 12:13:14.98765
    * 2012-01-10 12:13:14.98765+03:00
    * 2012-01-10 12:13:14.98765Z

    But also, some more odd ones (probably because of legacy):

    * 2012-01-10
    * ['2012-01-10', '12:13:14']

    """
    if date is None:
        return None
    if isinstance(date, datetime.datetime):
        if not date.tzinfo:
            date = date.replace(tzinfo=UTC)
        return date
    if isinstance(date, list):
        date = 'T'.join(date)
    if isinstance(date, str):
        if len(date) <= len('2000-01-01'):
            return (datetime.datetime
                    .strptime(date, '%Y-%m-%d')
                    .replace(tzinfo=UTC))
        else:
            try:
                parsed = isodate.parse_datetime(date)
            except ValueError:
                # e.g. '2012-01-10 12:13:14Z' becomes '2012-01-10T12:13:14Z'
                parsed = isodate.parse_datetime(
                    re.sub('(\d)\s(\d)', r'\1T\2', date)
                )
            if not parsed.tzinfo:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed
    raise ValueError("date not a parsable string")


def utc_now():
    """Return a timezone aware datetime instance in UTC timezone

    This funciton is mainly for convenience. Compare:

        >>> from antenna.util import utc_now
        >>> utc_now()
        datetime.datetime(2012, 1, 5, 16, 42, 13, 639834,
          tzinfo=<isodate.tzinfo.Utc object at 0x101475210>)

    Versus:

        >>> import datetime
        >>> from antenna.util import UTC
        >>> datetime.datetime.now(UTC)
        datetime.datetime(2012, 1, 5, 16, 42, 13, 639834,
          tzinfo=<isodate.tzinfo.Utc object at 0x101475210>)

    """
    return datetime.datetime.now(UTC)
