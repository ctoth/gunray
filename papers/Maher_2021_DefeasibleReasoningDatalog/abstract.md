# Abstract

## Original Text (Verbatim)
We address the problem of compiling defeasible theories to Datalog programs. We prove the correctness of a compilation, for the defeasible logic D(1,1), both directions, that we show to be linear in the size of the defeasible theory. Structural properties of D(1,1) are identified that support efficient implementations and/or approximations of the conclusions of defeasible theories via the logic, compared with other defeasible logics. We also provide well-studied structural properties of logic programs to adapt to incomplete Datalog implementations.

---

## Our Interpretation
Maher shows that defeasible logic D(1,1) can be mechanically compiled into standard Datalog-with-negation programs through metaprogram representation and fold/unfold transformations, with the compiled program being linear in the size of the original theory. The structural properties of the compiled program (call-consistency, stratification when the theory is hierarchical) enable leveraging existing, heavily-optimized Datalog engines rather than building bespoke defeasible reasoning implementations. This provides a principled bridge between the defeasible logic and logic programming communities.
