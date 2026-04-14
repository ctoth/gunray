"""Public package surface for Gunray."""

from .adapter import GunrayEvaluator
from .answer import Answer
from .arguments import Argument, build_arguments, is_subargument
from .defeasible import DefeasibleEvaluator
from .dialectic import (
    DialecticalNode,
    answer,
    blocking_defeater,
    build_tree,
    counter_argues,
    mark,
    proper_defeater,
    render_tree,
)
from .disagreement import complement, disagrees, strict_closure
from .evaluator import SemiNaiveEvaluator
from .preference import PreferenceCriterion, TrivialPreference
from .schema import DefeasibleModel, DefeasibleTheory, Model, Policy, Program, Rule
from .trace import (
    ClassificationTrace,
    DatalogTrace,
    DefeasibleTrace,
    ProofAttemptTrace,
    TraceConfig,
)

__all__ = [
    "Answer",
    "Argument",
    "ClassificationTrace",
    "DatalogTrace",
    "DefeasibleEvaluator",
    "DefeasibleModel",
    "DefeasibleTheory",
    "DefeasibleTrace",
    "DialecticalNode",
    "GunrayEvaluator",
    "Model",
    "Policy",
    "PreferenceCriterion",
    "ProofAttemptTrace",
    "Program",
    "Rule",
    "SemiNaiveEvaluator",
    "TraceConfig",
    "TrivialPreference",
    "answer",
    "blocking_defeater",
    "build_arguments",
    "build_tree",
    "complement",
    "counter_argues",
    "disagrees",
    "is_subargument",
    "mark",
    "proper_defeater",
    "render_tree",
    "strict_closure",
]
