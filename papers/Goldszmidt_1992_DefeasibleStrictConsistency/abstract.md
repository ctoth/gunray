# Abstract

## Original Text (Verbatim)
We propose a norm of consistency for a mixed set X of defeasible and strict sentences, based on a probabilistic interpretation of defaults. The criterion clearly delineates a clear distinction between knowledge base designing exceptions and cases containing outright contradictions. We then define a notion of entailment based on consistency and provide results that enable us to provide a characterization of the relation between consistency and entailment. We derive necessary and sufficient conditions for consistency, and provide a simple procedure for testing consistency. The procedure has a nice computational property: given a consistent subset X of X and identifying the inconsistent action of sentences of the first-case that X is not p-consistent. The same procedure can also be used to test whether a sentence is an exception or an inconsistency with respect to the sentences in X are if are Horn clauses, consistency and entailment can be tested in polynomial time.

---

## Our Interpretation
This paper formalizes the crucial distinction between "exceptions" (which are natural in defeasible reasoning) and "contradictions" (which indicate genuine database inconsistency) for mixed knowledge bases. The authors ground this in probabilistic semantics where defaults are high-probability conditionals, and provide a tractable testing procedure. The equivalence to System Z preferential semantics connects this work to the broader nonmonotonic reasoning landscape, making it foundational for any system that needs to manage coexisting defeasible and strict information.
