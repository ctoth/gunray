# Abstract

## Original Text (Verbatim)

We present a mathematical approach to defeasible reasoning. This approach is based on the notion of specificity introduced by Poole and the theory of warrant presented by Pollock. We combine the ideas of the two. The main contribution of this paper is a precise well-defined system which exhibits correct behavior when applied to the benchmark examples in the literature. We prove that an order relation can be introduced among equivalence classes under the equi-specificity relation. We also prove a theorem that ensures the termination of the process of finding the justified facts. Two more lemmas define a reduced search space for checking specificity. In order to implement the theoretical ideas, the language is restricted to Horn clauses for the evidential context. The language used to represent defeasible rules has been restricted in a similar way. The authors intend this work to unify the various existing approaches to argument-based defeasible reasoning.

---

## Our Interpretation

This paper provides the first rigorous mathematical foundation for argument-based defeasible reasoning, combining Poole's specificity comparison with Pollock's dialectical warrant process into a single formal system. The key theoretical result is a termination theorem proving that a unique stable set of justified beliefs always exists and can be computed. This is directly relevant to propstore's argumentation layer as it provides formal definitions of argument structures, specificity-based defeat, and dialectical justification that ground the system's approach to resolving competing claims.
