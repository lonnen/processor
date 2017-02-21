# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from functools import wraps
import gzip
import io
import json
import logging
import os
import re
import time
import uuid as uu

from contextlib import contextmanager

import isodate

UTC = isodate.UTC

logger = logging.getLogger(__name__)

defaultDepth = 2
oldHardDepth = 4

def createNewOoid(timestamp=None, depth=None):
    """Create a new Ooid for a given time, to be stored at a given depth
    timestamp: the year-month-day is encoded in the ooid. If none, use current day
    depth: the expected storage depth is encoded in the ooid. If non, use the defaultDepth
    returns a new opaque id string holding 24 random hex digits and encoded date and depth info
    """
    if not timestamp:
        timestamp = utc_now().date()
    if not depth:
        depth = defaultDepth
    assert depth <= 4 and depth >=1
    return "%s%d%02d%02d%02d" % (str(uu.uuid4())[:-7], depth,
        timestamp.year % 100, timestamp.month, timestamp.day)


def uuidToOoid(uuid, timestamp=None, depth=None):
    """ Create an ooid from a 32-hex-digit string in regular uuid format.
    uuid: must be uuid in expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxx7777777
    timestamp: the year-month-day is encoded in the ooid. If none, use current day
    depth: the expected storage depth is encoded in the ooid. If non, use the defaultDepth
    returns a new opaque id string holding the first 24 digits of the provided uuid and encoded date and depth info
    """
    if not timestamp:
        timestamp = utc_now().date()
    if not depth:
        depth = defaultDepth
    assert depth <= 4 and depth >=1
    return "%s%d%02d%02d%02d" % (uuid[:-7], depth,
        timestamp.year % 100, timestamp.month, timestamp.day)


def dateAndDepthFromOoid(ooid):
    """ Extract the encoded date and expected storage depth from an ooid.
    ooid: The ooid from which to extract the info
    returns (datetime(yyyy,mm,dd),depth) if the ooid is in expected format else (None,None)
    """
    year = month = day = None
    try:
        day = int(ooid[-2:])
    except:
        return None,None
    try:
        month = int(ooid[-4:-2])
    except:
        return None,None
    try:
        year = 2000 + int(ooid[-6:-4])
        depth = int(ooid[-7])
        if not depth: depth = oldHardDepth
        return (dt.datetime(year,month,day,tzinfo=UTC),depth)
    except:
        return None,None
    return None,None


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


def depthFromOoid(ooid):
    """Extract the encoded expected storage depth from an ooid.
    ooid: The ooid from which to extract the info
    returns expected depth if the ooid is in expected format else None
    """
    return dateAndDepthFromOoid(ooid)[1]


def dateFromOoid(ooid):
    """Extract the encoded date from an ooid.
    ooid: The ooid from which to extract the info
    returns encoded date if the ooid is in expected format else None
    """
    return dateAndDepthFromOoid(ooid)[0]


def datetimeFromISOdateString(s):
    """Take an ISO date string of the form YYYY-MM-DDTHH:MM:SS.S
    and convert it into an instance of datetime.datetime
    """
    return string_to_datetime(s)


def datestring_to_weekly_partition(date_str):
    """Return a string representing a weekly partition from a date.

    Our partitions start on Mondays.

    Example:
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


@contextmanager
def temp_file_context(raw_dump_path):
    """this contextmanager implements conditionally deleting a pathname
    at the end of a context if the pathname indicates that it is a temp
    file by having the word 'TEMPORARY' embedded in it."""
    try:
        yield raw_dump_path
    finally:
        if 'TEMPORARY' in raw_dump_path:
            try:
                os.unlink(raw_dump_path)
            except OSError:
                logger.warning(
                    'unable to delete %s. manual deletion is required.',
                    raw_dump_path,
                    exc_info=True
                )


def uuid_to_date(uuid, century='20'):
    """Return a date created from the last 6 digits of a uuid.

    Arguments:
        uuid The unique identifier to parse.
        century The first 2 digits to assume in the year. Default is '20'.

    Examples:
        >>> uuid_to_date('e8820616-1462-49b6-9784-e99a32120201')
        datetime.date(2012, 2, 1)

        >>> uuid_to_date('e8820616-1462-49b6-9784-e99a32120201', '18')
        datetime.date(1812, 2, 1)

    """
    day = int(uuid[-2:])
    month = int(uuid[-4:-2])
    year = int('%s%s' % (century, uuid[-6:-4]))

    return datetime.date(year=year, month=month, day=day)


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
