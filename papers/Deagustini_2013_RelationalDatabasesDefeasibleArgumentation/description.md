---
tags: [defeasible-argumentation, databases, DeLP]
---
Presents DB-DeLP, a framework that connects Defeasible Logic Programming (DeLP) to relational databases via a translation layer (Target Connections, Data Source Retrieval Functions), enabling defeasible argumentation over dynamically retrieved structured data. Empirical evaluation shows linear scaling with database size for simple queries, with the main bottleneck being data retrieval rather than dialectical analysis. Relevant to propstore as an architectural pattern for connecting argumentation engines to external structured data sources, though it uses DeLP rather than ASPIC+.
