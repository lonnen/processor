import logging

from everett.component import ConfigOptions, RequiredConfigMixin

logger = logging.getLogger(__name__)

def parse_attribute(val):
    module, attribute_name = val.rsplit('.', 1)
    module = importlib.import_module(module)
    try:
        return getattr(module, attribute_name)
    except AttributeError:
        raise ValueError(
            '%s is not a valid attribute of %s' %
            (attribute_name, module)
        )

mozilla_rules = [
    # rules to change the internals of the raw crash
    "socorro.processor.mozilla_transform_rules.ProductRewrite",
    "socorro.processor.mozilla_transform_rules.ESRVersionRewrite",
    "socorro.processor.mozilla_transform_rules.PluginContentURL",
    "socorro.processor.mozilla_transform_rules.PluginUserComment",
    "socorro.processor.mozilla_transform_rules.FennecBetaError20150430",
    # rules to transform a raw crash into a processed crash
    "socorro.processor.general_transform_rules.IdentifierRule",
    "socorro.processor.breakpad_transform_rules.BreakpadStackwalkerRule2015",
    "socorro.processor.mozilla_transform_rules.ProductRule",
    "socorro.processor.mozilla_transform_rules.UserDataRule",
    "socorro.processor.mozilla_transform_rules.EnvironmentRule",
    "socorro.processor.mozilla_transform_rules.PluginRule",
    "socorro.processor.mozilla_transform_rules.AddonsRule",
    "socorro.processor.mozilla_transform_rules.DatesAndTimesRule",
    "socorro.processor.mozilla_transform_rules.OutOfMemoryBinaryRule",
    "socorro.processor.mozilla_transform_rules.JavaProcessRule",
    "socorro.processor.mozilla_transform_rules.Winsock_LSPRule",
    # post processing of the processed crash
    "socorro.processor.breakpad_transform_rules.CrashingThreadRule",
    "socorro.processor.general_transform_rules.CPUInfoRule",
    "socorro.processor.general_transform_rules.OSInfoRule",
    "socorro.processor.mozilla_transform_rules.BetaVersionRule",
    "socorro.processor.mozilla_transform_rules.ExploitablityRule",
    "socorro.processor.mozilla_transform_rules.FlashVersionRule",
    "socorro.processor.mozilla_transform_rules.OSPrettyVersionRule",
    "socorro.processor.mozilla_transform_rules.TopMostFilesRule",
    "socorro.processor.mozilla_transform_rules.MissingSymbolsRule",
    "socorro.processor.mozilla_transform_rules.ThemePrettyNameRule",
    "socorro.processor.signature_utilities.SignatureGenerationRule,"
    "socorro.processor.signature_utilities.StackwalkerErrorSignatureRule",
    "socorro.processor.signature_utilities.OOMSignature",
    "socorro.processor.signature_utilities.AbortSignature",
    "socorro.processor.signature_utilities.SignatureShutdownTimeout",
    "socorro.processor.signature_utilities.SignatureRunWatchDog",
    "socorro.processor.signature_utilities.SignatureIPCChannelError",
    "socorro.processor.signature_utilities.SignatureIPCMessageName",
    "socorro.processor.signature_utilities.SigTrunc",
    # a set of classifiers for support
    "socorro.processor.support_classifiers.BitguardClassifier",
    "socorro.processor.support_classifiers.OutOfDateClassifier",
    # a set of classifiers to help with jit crashes
    "socorro.processor.breakpad_transform_rules.JitCrashCategorizeRule",
    "socorro.processor.signature_utilities.SignatureJitCategory",
    # a set of special request classifiers
    "socorro.processor.skunk_classifiers.DontConsiderTheseFilter",
    # currently not in use, anticipated to be re-enabled in the future
    #"socorro.processor.skunk_classifiers.UpdateWindowAttributes",
    "socorro.processor.skunk_classifiers.SetWindowPos",
    # currently not in use, anticipated to be re-enabled in the future
    #"socorro.processor.skunk_classifiers.SendWaitReceivePort",
    # currently not in use, anticipated to be re-enabled in the future
    #"socorro.processor.skunk_classifiers.Bug811804",
    # currently not in use, anticipated to be re-enabled in the future
    #"socorro.processor.skunk_classifiers.Bug812318",
    "socorro.processor.skunk_classifiers.NullClassification"
]

class Rule(RequiredConfigMixin):
    """the base class for Support Rules.  It provides the framework for the
    rules 'predicate', 'action', and 'version' as well as utilites to help
    rules do their jobs."""

    required_config = ConfigOptions()
    required_config.add_option(
        'chatty',
        default=False,
        doc='should this rule announce what it is doing?'
    )

    def predicate(self, *args, **kwargs):
        """the default predicate for Support Classifiers invokes any derivied
        _predicate function, trapping any exceptions raised in the process.  We
        are obligated to catch these exceptions to give subsequent rules the
        opportunity to act.  An error during the predicate application is a
        failure of the rule, not a failure of the classification system itself
        """
        try:
            return self._predicate(*args, **kwargs)
        except Exception as x:
            logger.debug(
                'Rule %s predicicate failed because of "%s"',
                str(self.__class__),
                x,
                exc_info=True
            )
            return False

    def _predicate(self, *args, **kwargs):
        """"The default support classifier predicate just returns True.  We
        want all the support classifiers run.

        returns:
            True - this rule should be applied
            False - this rule should not be applied
        """
        return True

    def action(self, *args, **kwargs):
        """the default action for Support Classifiers invokes any derivied
        _action function, trapping any exceptions raised in the process.  We
        are obligated to catch these exceptions to give subsequent rules the
        opportunity to act and perhaps mitigate the error.  An error during the
        action application is a failure of the rule, not a failure of the
        classification system itself."""
        try:
            return self._action(*args, **kwargs)
        except KeyError as x:
            logger.debug(
                'Rule %s action failed because of missing key "%s"',
                str(self.__class__),
                x,
            )
        except Exception as x:
            logger.debug(
                'Rule %s action failed because of "%s"',
                str(self.__class__),
                x,
                exc_info=True
            )
        return False

    def _action(self, *args, **kwargs):
        """Rules derived from this base class ought to override this method
        with an actual classification rule.  Successful application of this
        method should include a call to '_add_classification'.

        returns:
            True - this rule was applied successfully and no further rules
                   should be applied
            False - this rule did not succeed and further rules should be
                    tried
        """
        return True

    def version(self):
        """This method should be overridden in a derived class."""
        return '0.0'

    def act(self, *args, **kwargs):
        """gather a rules parameters together and run the predicate. If that
        returns True, then go on and run the action function

        returns:
            a tuple indicating the results of applying the predicate and the
            action function:
               (False, None) - the predicate failed, action function not run
               (True, True) - the predicate and action functions succeeded
               (True, False) - the predicate succeeded, but the action function
                               failed"""
        if self.predicate(*args, **kwargs):
            bool_result = self.action(*args, **kwargs)
            return (True, bool_result)
        else:
            return (False, None)


class RuleEngine(RequiredConfigMixin):
    """
    """

    required_config = ConfigOptions()
    required_config.add_option(
        'transformation_rules',
        default='processor.rule_engine.mozilla_rules',
        doc='Python dotted path to ruleset',
        parser=parse_attribute
    )

    def __init__(self, config):
        self.config = config.with_options(self)
        self.rules = self.config('transformation_rules')

    def transform(self, ):

        # rule application: "socorrolib.lib.transform_rules.TransformRuleSystem"

        # RULE SYSTEM
        # taken from Processor2015.default_rule_set

        # Rule sets are defined as lists of lists (or tuples).  As they will be loaded
        # from json, they will always come in a lists rather than tuples. Arguably,
        # tuples may be more appropriate, but really, they can be anything iterable.

        # The outermost sequence is a list of rule sets.  There can be any number of
        # them and can be organized at will.  The example below shows an organization
        # by processing stage: pre-processing the raw_crash, converter raw to
        # processed, and post-processing the processed_crash.

        # Each rule set is defined by five elements:
        #    rule name: any useful string
        #    tag: a categorization system, programmer defined system (for future)
        #    rule set class: the fully qualified name of the class that implements
        #                    the rule application process.  On the introduction of
        #                    Processor2015, the only option is the one in the example.
        #    rule list: a comma delimited list of fully qualified class names that
        #               implement the individual transformation rules.  The API that
        #               these classes must conform to is defined by the rule base class
        #               socorrolib.lib.transform_rules.Rule
        default_rules = [
            # rules to change the internals of the raw crash
            # rules to transform a raw crash into a processed crash
            # post processing of the processed crash
            [
                "raw_transform",  # name of the rule
                "processor.json_rewrite",  # a tag in a dotted-form
                "socorrolib.lib.transform_rules.TransformRuleSystem",  # rule set class
                "apply_all_rules",  # rule set class method to apply rules
                ""  # comma delimited list of fully qualified rule class names
            ],
            [   # rules to transform a raw crash into a processed crash
                "raw_to_processed_transform",
                "processer.raw_to_processed",
                "socorrolib.lib.transform_rules.TransformRuleSystem",
                "apply_all_rules",
                ""
            ],
            [   # post processing of the processed crash
                "processed_transform",
                "processer.processed",
                "socorrolib.lib.transform_rules.TransformRuleSystem",
                "apply_all_rules",
                ""
            ],
        ]
        rule_sets = default_rule_set

        rule_system = {}
        for a_rule_set in rule_sets:
            # TODO: logger
            rule_system[a_rule_set[0]] = (
                a_rule_set[2]
            )
        pass
