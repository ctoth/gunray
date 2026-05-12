"""Public package surface for Gunray."""

from .adapter import GunrayEvaluator
from .answer import Answer
from .anytime import EnumerationExceeded
from .arguments import Argument, build_arguments, is_subargument
from .consistency import (
    ConditionalDatabase,
    ConditionalSentence,
    ConsistencyReport,
    analyze_p_consistency,
    strictly_p_entails,
)
from .defeasible import DefeasibleEvaluator
from .dialectic import (
    DialecticalNode,
    answer,
    blocking_defeater,
    build_tree,
    classify_defeat,
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
    compute_non_approximated,
    inspect_grounding,
)
from .parser import parse_atom_text
from .preference import (
    CompositePreference,
    GeneralizedSpecificity,
    PreferenceComparison,
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
    GarciaSections,
    GroundingMode,
    MarkingPolicy,
    Model,
    NegationSemantics,
    Program,
    ProjectionSemantics,
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
    "ConditionalDatabase",
    "ConditionalSentence",
    "ConsistencyReport",
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
    "GarciaSections",
    "GeneralizedSpecificity",
    "GroundAtom",
    "GroundDefeasibleRule",
    "GroundRuleInstance",
    "GroundRuleResolution",
    "GroundingInspection",
    "GroundingMode",
    "GroundingSimplification",
    "GunrayEvaluator",
    "MarkingPolicy",
    "Model",
    "NegationSemantics",
    "PreferenceComparison",
    "PreferenceCriterion",
    "Program",
    "ProjectionSemantics",
    "Rule",
    "Scalar",
    "SemiNaiveEvaluator",
    "SuperiorityPreference",
    "TraceConfig",
    "TrivialPreference",
    "Variable",
    "answer",
    "analyze_p_consistency",
    "blocking_defeater",
    "build_arguments",
    "build_tree",
    "classify_defeat",
    "complement",
    "compute_non_approximated",
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
    "strictly_p_entails",
]
