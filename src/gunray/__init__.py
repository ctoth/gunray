"""Public package surface for Gunray."""

from .adapter import GunrayEvaluator
from .answer import Answer
from .arguments import Argument, is_subargument
from .defeasible import DefeasibleEvaluator
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
    "DefeasibleModel",
    "DatalogTrace",
    "DefeasibleEvaluator",
    "DefeasibleTheory",
    "DefeasibleTrace",
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
    "is_subargument",
]
