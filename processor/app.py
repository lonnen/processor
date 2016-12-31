# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from pathlib import Path

import logging
import logging.config

from processor.rule import UUIDCorrection, CreateMetadata, SaveMetadata
from processor.rules.mozilla_transform_rules import (
    ESRVersionRewrite,
    PluginContentURL,
    PluginUserComment,
    ProductRewrite,
    ProductRule,
)

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
                # s.p.general_transform_rules.IdentifierRule
                # s.p.breakpad_transform_rules.BreakpadStackwalkerRule2015
                ProductRule(),
                # s.p.mozilla_transform_rules.UserDataRule
                # s.p.mozilla_transform_rules.EnvironmentRule
                # s.p.mozilla_transform_rules.PluginRule
                # s.p.mozilla_transform_rules.AddonsRule
                # s.p.mozilla_transform_rules.DatesAndTimesRule
                # s.p.mozilla_transform_rules.OutOfMemoryBinaryRule
                # s.p.mozilla_transform_rules.JavaProcessRule
                # s.p.mozilla_transform_rules.Winsock_LSPRule

                # post processing of the processed crash
                #
                # s.p.breakpad_transform_rules.CrashingThreadRule
                # s.p.general_transform_rules.CPUInfoRule
                # s.p.general_transform_rules.OSInfoRule
                # s.p.mozilla_transform_rules.BetaVersionRule
                # s.p.mozilla_transform_rules.ExploitablityRule
                # s.p.mozilla_transform_rules.FlashVersionRule
                # s.p.mozilla_transform_rules.OSPrettyVersionRule
                # s.p.mozilla_transform_rules.TopMostFilesRule
                # s.p.mozilla_transform_rules.MissingSymbolsRule
                # s.p.mozilla_transform_rules.ThemePrettyNameRule
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
