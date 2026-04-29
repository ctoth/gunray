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
from .grounding import (
    GroundingInspection,
    GroundingSimplification,
    GroundRuleInstance,
    GroundRuleResolution,
    inspect_grounding,
)
from .parser import parse_atom_text
from .preference import (
    CompositePreference,
    GeneralizedSpecificity,
    PreferenceCriterion,
    SuperiorityPreference,
    TrivialPreference,
)
from .schema import (
    ClosurePolicy,
    DefeasibleModel,
    DefeasibleSections,
    DefeasibleTheory,
    FactTuple,
    MarkingPolicy,
    Model,
    NegationSemantics,
    Program,
    Rule,
    Scalar,
)
from .trace import (
    DatalogTrace,
    DefeasibleTrace,
    TraceConfig,
)
from .types import Constant, GroundAtom, GroundDefeasibleRule, Variable

__all__ = [
    "Answer",
    "Argument",
    "ClosurePolicy",
    "CompositePreference",
    "Constant",
    "DatalogTrace",
    "DefeasibleEvaluator",
    "DefeasibleModel",
    "DefeasibleSections",
    "DefeasibleTheory",
    "DefeasibleTrace",
    "DialecticalNode",
    "DuplicateRuleId",
    "EnumerationExceeded",
    "FactTuple",
    "GeneralizedSpecificity",
    "GroundAtom",
    "GroundDefeasibleRule",
    "GroundRuleInstance",
    "GroundRuleResolution",
    "GroundingInspection",
    "GroundingSimplification",
    "GunrayEvaluator",
    "MarkingPolicy",
    "Model",
    "NegationSemantics",
    "PreferenceCriterion",
    "Program",
    "Rule",
    "Scalar",
    "SemiNaiveEvaluator",
    "SuperiorityPreference",
    "TraceConfig",
    "TrivialPreference",
    "Variable",
    "answer",
    "blocking_defeater",
    "build_arguments",
    "build_tree",
    "complement",
    "counter_argues",
    "disagrees",
    "explain",
    "inspect_grounding",
    "is_subargument",
    "mark",
    "parse_atom_text",
    "proper_defeater",
    "render_tree",
    "render_tree_mermaid",
    "strict_closure",
]
