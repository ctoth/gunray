---
tags: [defeasible-reasoning, argumentation, specificity, warrant, non-monotonic-logic]
---
Presents a rigorous mathematical framework for defeasible argumentation that combines Poole's specificity criterion with Pollock's theory of warrant, defining argument structures, a specificity partial order, disagreement/counterargument/defeat relations, and a dialectical justification process that converges to a unique stable set of justified beliefs.
The paper proves termination and provides search-space reduction lemmas, then implements the theory as "jf," a Prolog-based defeasible reasoning system that correctly handles all standard benchmark examples (Opus, Nixon Diamond, Cascaded Ambiguities, Royal African Elephants).
Foundational for propstore's argumentation layer: the formal definitions of argument structures, specificity-based defeat, and dialectical levels directly ground how competing claims should be resolved, and the unique stable set theorem guarantees deterministic computation.
