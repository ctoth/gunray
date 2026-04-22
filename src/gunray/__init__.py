"""Public package surface for Gunray."""

from .adapter import GunrayEvaluator
from .answer import Answer
from .anytime import EnumerationExceeded
from .arguments import Argument, build_arguments, is_subargument
from .defeasible import DefeasibleEvaluator
from .dialectic import (
    DialecticalNode,
    answer,
    blocking_defeater,
    build_tree,
    counter_argues,
    explain,
    mark,
    proper_defeater,
    render_tree,
    render_tree_mermaid,
)
from .disagreement import complement, disagrees, strict_closure
from .errors import DuplicateRuleId
from .evaluator import SemiNaiveEvaluator
from .preference import (
    CompositePreference,
    GeneralizedSpecificity,
    PreferenceCriterion,
    SuperiorityPreference,
    TrivialPreference,
)
from .schema import (
    DefeasibleModel,
    DefeasibleTheory,
    Model,
    NegationSemantics,
    Policy,
    Program,
    Rule,
)
from .trace import (
    DatalogTrace,
    DefeasibleTrace,
    TraceConfig,
)
from .types import GroundDefeasibleRule

__all__ = [
    "Answer",
    "Argument",
    "CompositePreference",
    "DatalogTrace",
    "DefeasibleEvaluator",
    "DefeasibleModel",
    "DefeasibleTheory",
    "DefeasibleTrace",
    "DialecticalNode",
    "DuplicateRuleId",
    "EnumerationExceeded",
    "GeneralizedSpecificity",
    "GroundDefeasibleRule",
    "GunrayEvaluator",
    "Model",
    "NegationSemantics",
    "Policy",
    "PreferenceCriterion",
    "Program",
    "Rule",
    "SemiNaiveEvaluator",
    "SuperiorityPreference",
    "TraceConfig",
    "TrivialPreference",
    "answer",
    "blocking_defeater",
    "build_arguments",
    "build_tree",
    "complement",
    "counter_argues",
    "disagrees",
    "explain",
    "is_subargument",
    "mark",
    "proper_defeater",
    "render_tree",
    "render_tree_mermaid",
    "strict_closure",
]
