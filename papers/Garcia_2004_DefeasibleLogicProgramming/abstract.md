# Abstract

## Original Text (Verbatim)

The work reported here introduces Defeasible Logic Programming (DeLP), a formalism that combines results of Logic Programming and Defeasible Argumentation. DeLP provides the possibility of representing information tentatively, in the form of weak rules, which can be used to build arguments for or against a given goal. A dialectical process determines which arguments are ultimately accepted. The language used for knowledge representation extends the language of logic programming, incorporating a defeasible operator in order to distinguish between strict and defeasible knowledge. A defeasible derivation is defined as the construction of an argument by chaining applications of defeasible rules. The definition of argument, counter-argument and defeat is given in terms of defeasible derivations. A dialectical analysis is performed in order to determine if a given argument is defeated. The resulting dialectical trees can be used to determine whether a literal is warranted.

---

## Our Interpretation

This paper solves the problem of how to combine Prolog-style logic programming with defeasible argumentation: how to represent both certain and tentative knowledge, build arguments from rules, handle conflicts between arguments, and determine which conclusions are ultimately warranted. The key contribution is the dialectical tree mechanism that considers all possible counter-arguments simultaneously and produces a four-valued answer (YES/NO/UNDECIDED/UNKNOWN). This is directly relevant to propstore because it provides a concrete, implemented algorithm for the kind of rule-based defeasible reasoning propstore needs in its argumentation layer, with formal guarantees against pathological reasoning patterns.
