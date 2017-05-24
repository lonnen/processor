# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import wraps
import logging
import logging.config
from pathlib import Path
import socket

from everett.manager import ConfigManager, ConfigEnvFileEnv, ConfigOSEnv, ListOf, parse_class
from everett.component import ConfigOptions, RequiredConfigMixin
import markus

from processor.rule import UUIDCorrection, CreateMetadata, SaveMetadata
from processor.rules.general_transform_rules import (
    CPUInfoRule,
    IdentifierRule,
    OSInfoRule
)
from processor.rules.mozilla_transform_rules import (
    AddonsRule,
    DatesAndTimesRule,
    EnvironmentRule,
    ESRVersionRewrite,
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


logger = logging.getLogger(__name__)


def setup_logging(app_config):
    """Initializes Python logging configuration"""
    host_id = app_config('host_id') or socket.gethostname()

    class AddHostID(logging.Filter):
        def filter(self, record):
            record.host_id = host_id
            return True

    dc = {
        'version': 1,
        'disable_existing_loggers': True,
        'filters': {
            'add_hostid': {
                '()': AddHostID
            }
        },
        'formatters': {
            'mozlog': {
                '()': 'dockerflow.logging.JsonLogFormatter',
                'logger_name': 'antenna'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'filters': ['add_hostid'],
            },
            'mozlog': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'mozlog',
                'filters': ['add_hostid'],
            },
        },
        'root': {
            'handlers': ['mozlog'],
            'level': 'WARNING',
        },
        'loggers': {
            'processor': {
                'propagate': False,
                'handlers': ['mozlog'],
                'level': app_config('logging_level'),
            },
            'markus': {
                'propagate': False,
                'handlers': ['console'],
                'level': 'INFO',
            },
        },
    }
    logging.config.dictConfig(dc)


def setup_metrics(metrics_classes, config, logger=None):
    """Initializes the metrics system"""
    logger.info('Setting up metrics: %s', metrics_classes)

    markus_configuration = []
    for cls in metrics_classes:
        backend = cls(config)
        log_config(logger, backend)
        markus_configuration.append(backend.to_markus())

    markus.configure(markus_configuration)


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

        if 'secret' in opt.key.lower() and val:
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
    required_config.add_option(
        'metrics_class',
        default='processor.metrics.LoggingMetrics',
        doc=(
            'Comma-separated list of metrics backends to use. Possible options: '
            '"processor.metrics.LoggingMetrics" and "processor.metrics.DatadogMetrics"',
        ),
        parser=ListOf(parse_class)
    )
    required_config.add_option(
        'secret_sentry_dsn',
        default='',
        doc=(
            'Sentry DSN to use. See https://docs.sentry.io/quickstart/#configure-the-dsn '
            'for details. If this is not set an unhandled exception logging middleware '
            'will be used instead.'
        )
    )
    required_config.add_option(
        'host_id',
        default='',
        doc=(
            'Identifier for the host that is running Antenna. This identifies this Antenna '
            'instance in the logs and makes it easier to correlate Antenna logs with '
            'other data. For example, the value could be a public hostname, an instance id, '
            'or something like that. If you do not set this, then socket.gethostname() is '
            'used instead.'
        )
    )

    def __init__(self, config):
        self.config_manager = config
        self.config = config.with_options(self)

    def __call__(self, key):
        return self.config(key)


class Processor:
    def __init__(self, config):
        self.config = config

    # FIXME(willkg): this is all prototypey filler
    def main(self, crash_id):
        # while True:
        try:
            Crash(crash_id).fetch().pipeline(
                # initialize
                UUIDCorrection(),
                CreateMetadata(),

                # rules to change the internals of the raw crash
                ProductRewrite(),
                ESRVersionRewrite(),
                PluginContentURL(),
                PluginUserComment(),
                FennecBetaError20150430(),

                # rules to transform a raw crash into a processed crash
                #
                IdentifierRule(),
                # s.p.breakpad_transform_rules.BreakpadStackwalkerRule2015
                ProductRule(),
                UserDataRule(),
                EnvironmentRule(),
                PluginRule(),
                AddonsRule(),
                DatesAndTimesRule(),
                # s.p.mozilla_transform_rules.OutOfMemoryBinaryRule
                JavaProcessRule(),
                Winsock_LSPRule(),

                # post processing of the processed crash
                #
                # s.p.breakpad_transform_rules.CrashingThreadRule
                CPUInfoRule(),
                OSInfoRule(),
                # s.p.mozilla_transform_rules.BetaVersionRule(),
                ExploitablityRule(),
                FlashVersionRule(),
                # s.p.mozilla_transform_rules.OSPrettyVersionRule
                TopMostFilesRule(),
                # s.p.mozilla_transform_rules.MissingSymbolsRule
                ThemePrettyNameRule(),

                # s.p.signature_utilities.SignatureGenerationRule
                # s.p.signature_utilities.StackwalkerErrorSignatureRule
                # s.p.signature_utilities.OOMSignature
                # s.p.signature_utilities.AbortSignature
                # s.p.signature_utilities.SignatureShutdownTimeout
                # s.p.signature_utilities.SignatureRunWatchDog
                # s.p.signature_utilities.SignatureIPCChannelError
                # s.p.signature_utilities.SignatureIPCMessageName
                # s.p.signature_utilities.SigTrunc

                # a set of classfiers for support
                # TODO: this was apply_until_action_succeeds
                #
                # s.p.support_classifiers.BitguardClassifier
                # s.p.support_classifiers.OutOfDateClassifier

                # a set of classifiers t help with jit crashes
                #
                # s.p.breakpad_transform_rules.JitCrashCategorizeRule
                # s.p.signature_utilities.SignatureJitCategory

                # a set of special request classifiers
                # TODO: this was apply_until_action_succeeds
                #
                # s.p.skunk_classifiers.DontConsiderTheseFilter
                # s.p.skunk_classifiers.SetWindowPos
                # s.p.skunk_classifiers.NullClassification

                # finalize
                SaveMetadata(),
            ).save()
        finally:
            # TODO: clean up any temp files, dumps, etc
            pass
