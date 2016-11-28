# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from pathlib import Path

import logging
import logging.config


from everett.component import ConfigOptions, RequiredConfigMixin

logger = logging.getLogger(__name__)

def setup_logging(logging_level):
    """Initializes Python logging configuration"""
    dc = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'development': {
                'format': '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S %z',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'development',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'loggers': {
            'processor': {
                'propagate': False,
                'handlers': ['console'],
                'level': logging_level,
            },
        },
    }
    logging.config.dictConfig(dc)


def log_unhandled(fun):
    @wraps(fun)
    def _log_unhandled(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except Exception:
            logger.exception('UNHANDLED EXCEPTION!')
            raise

    return _log_unhandled

def log_config(logger, component):
    for namespace, key, val, opt in component.get_runtime_config():
        if namespace:
            namespaced_key = '%s_%s' % ('_'.join(namespace), key)
        else:
            namespaced_key = key

        namespaced_key = namespaced_key.upper()

        if 'secret' in opt.key.lower():
            msg = '%s=*****' % namespaced_key
        else:
            msg = '%s=%s' % (namespaced_key, val)
        logger.info(msg)

class AppConfig(RequiredConfigMixin):
    """Application-level config

    To pull out a config item, you can do this::

        config = ConfigManager([ConfigOSEnv()])
        app_config = AppConfig(config)

        debug = app_config('debug')


    To create a component with configuration, you can do this::

        class SomeComponent(RequiredConfigMixin):
            required_config = ConfigOptions()

            def __init__(self, config):
                self.config = config.with_options(self)

        some_component = SomeComponent(app_config.config)


    To pass application-level configuration to components, you should do it
    through arguments like this::

        class SomeComponent(RequiredConfigMixin):
            required_config = ConfigOptions()

            def __init__(self, config, debug):
                self.config = config.with_options(self)
                self.debug = debug

        some_component = SomeComponent(app_config.config_manager, debug)

    """
    required_config = ConfigOptions()
    required_config.add_option(
        'basedir',
        default=str(Path(__file__).parent.parent),
        doc='The root directory for this application to find and store things.'
    )
    required_config.add_option(
        'logging_level',
        default='DEBUG',
        doc='The logging level to use. DEBUG, INFO, WARNING, ERROR or CRITICAL'
    )


    def __init__(self, config):
        self.config_manager = config
        self.config = config.with_options(self)

    def __call__(self, key):
        return self.config(key)


class Processor:
    def __init__(self, config):
        pass

    def main(self, crash_id):
        # while True:
        try:
            save(transform(fetch(crash_id)))
        finally:
            # TODO: clean up any temp files, dumps, etc
            pass


    def fetch(self, crash_id):
        """Attempt to fetch everything we know about a crash_id.

        If the raw_crash or raw_dumps cannot be found, abort.
        If the processed_crash exists, reuse that, else creat one.
        """
        # TODO: implement get_raw_crash, get_raw_dumps_as_files
        # TODO: clean this up
        try:
            # socorro/external/boto/BotoCrashStorage.get_raw_crash()
            raw_crash = get_raw_crash(crash_id)
            # socorro/external/boto/BotoCrashStorage.get_raw_dumps_as_files()
            dumps = get_raw_dumps_as_files(crash_id)
            try:
                # socorro/external/boto/BotoCrashStorage.get_unredacted_processed()
                processed_crash = get_unredacted_processed(crash_id)
            except CrashIDNotFound:
                processed_crash = DotDict()
        except CrashIDNotFound:
            _reject(crash_id, 'CrashIDNotFound') # from processor2015/processor_2015.py
        except Exception:
            _reject(crash_id, 'error loading crash')
        return raw_crash, dumps, processed_crash

    def _reject(crash_id, reason):
        logger.warning("%s rejected: %s", crash_id, reason)


    def transform(self, raw_crash, dumps, processed_crash):
        """business logic to modify dumps and raw crash into a final
        processed crash form"""

        if 'uuid' not in raw_crash:
            # TODO: previously this set raw_crash.uuid = crash_id
            # TODO: probably should be an error condition instead
            pass

        # Processor2015.__init__()
        # deleted: quit_check_callback system

        # RULE SYSTEM
        # taken from Processor2015.default_rule_set
        # see processor.rule_engine

        # Processor2015.process_crash(
        raw_crash = raw_crash
        raw_dumps = dumps
        processed_crash = processed_crash
        #)

        """Take a raw_crash and its associated raw_dumps and return a
        processed_crash.
        """
        # processor_meta_data will be used to ferry "inside information" to
        # transformation rules.  Sometimes rules need a bit more extra
        # information about the transformation process itself.
        #
        # TODO: revisit this setup block, which is likely unecessary
        # once rules are set up
        processor_meta_data = DotDict()
        processor_meta_data.processor_notes = [
            self.config.processor_name,
            self.__class__.__name__
        ]
        processor_meta_data.quit_check = self.quit_check
        processor_meta_data.processor = self
        processor_meta_data.config = self.config

        if "processor_notes" in processed_crash:
            original_processor_notes = [
                x.strip() for x in processed_crash.processor_notes.split(";")
            ]
            processor_meta_data.processor_notes.append(
                "earlier processing: %s" % processed_crash.get(
                    "started_datetime",
                    'Unknown Date'
                )
            )
        else:
            original_processor_notes = []

        processed_crash.success = False
        processed_crash.started_datetime = utc_now()
        # for backwards compatibility:
        processed_crash.startedDateTime = processed_crash.started_datetime
        processed_crash.signature = 'EMPTY: crash failed to process'

        crash_id = raw_crash.get('uuid', 'unknown')
        try:
            # quit_check calls ought to be scattered around the code to allow
            # the processor to be responsive to requests to shut down.
            # quit_check()

            processor_meta_data.started_timestamp = self._log_job_start(
                crash_id
            )

            # apply transformations
            #    step through each of the rule sets to apply the rules.
            for a_rule_set_name, a_rule_set in self.rule_system.iteritems():
                # for each rule set, invoke the 'act' method - this method
                # will be the method specified in fourth element of the
                # rule set configuration list.
                a_rule_set.act(
                    raw_crash,
                    raw_dumps,
                    processed_crash,
                    processor_meta_data
                )
                quit_check()

            # the crash made it through the processor rules with no exceptions
            # raised, call it a success.
            processed_crash.success = True

        except Exception as x:
            self.config.logger.warning(
                'Error while processing %s: %s',
                crash_id,
                str(x),
                exc_info=True
            )
            processor_meta_data.processor_notes.append(
                'unrecoverable processor error: %s' % x
            )

        # the processor notes are in the form of a list.  Join them all
        # together to make a single string
        processor_meta_data.processor_notes.extend(original_processor_notes)
        processed_crash.processor_notes = '; '.join(
            processor_meta_data.processor_notes
        )
        completed_datetime = utc_now()
        processed_crash.completed_datetime = completed_datetime
        # for backwards compatibility:
        processed_crash.completeddatetime = completed_datetime

        self._log_job_end(
            processed_crash.success,
            crash_id
        )

        return raw_crash, dumps, processed_crash


    def save(raw_crash, dumps, processed_crash):
        """write the modified crashes"""

        # bug 866973 - save_raw_and_processed() instead of just
        # save_processed().  The raw crash may have been modified
        # by the processor rules.  The individual crash storage
        # implementations may choose to honor re-saving the raw_crash
        # or not.

        # TODO replace this crashstorage class
        self.destination.save_raw_and_processed(
            raw_crash,
            None,
            processed_crash,
            crash_id
        )
        logger.info('saved - %s', crash_id)
