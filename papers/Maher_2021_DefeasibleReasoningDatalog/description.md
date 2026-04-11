---
tags: [defeasible-logic, datalog, compilation, well-founded-semantics, logic-programming]
---
This paper compiles defeasible logic D(1,1) into standard Datalog-with-negation programs using metaprogram representation and unfold/fold transformations, proving the compilation is correct and linear in size. Key findings include that structural properties (stratification, call-consistency, range-restriction) transfer from the defeasible theory to the compiled program, enabling execution on existing Datalog engines like XSB and DLV. Relevant to propstore as an alternative compilation path for rule-based defeasible reasoning that could complement the existing ASPIC+ argumentation layer, particularly for performance-critical evaluation of large rule sets under well-founded semantics.
