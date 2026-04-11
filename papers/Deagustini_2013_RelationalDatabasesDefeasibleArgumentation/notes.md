---
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-10T17:12:37Z"
---
# Relational Databases as a Massive Information Source for Defeasible Argumentation

- **Title:** Relational databases as a massive information source for defeasible argumentation
- **Authors:** Cristian A.D. Deagustini, Santiago E. Fulladoza Dalibón, Sebastián Gottifredi, Marcelo A. Falappa, Carlos I. Chesñevar, Guillermo R. Simari
- **Year:** 2013
- **Venue:** Knowledge-Based Systems 51, pp. 93-109
- **DOI:** 10.1016/j.knosys.2013.07.010

## One-Sentence Summary

Presents a framework (DB-DeLP) that integrates relational databases as massive external data sources into Defeasible Logic Programming (DeLP), enabling defeasible argumentation over structured data retrieved via SQL queries.

## Problem Addressed

Traditional argumentation systems build arguments from facts stored in a single, fixed knowledge base, which is not feasible for real-world environments with large amounts of data in relational databases *(p.0)*. The challenge is how to connect DeLP's inference engine with external relational databases so that data can be dynamically retrieved, translated into DeLP predicates, and used in defeasible argumentation without requiring all data to be pre-loaded *(p.0-1)*.

## Key Contributions

1. **DB-DeLP framework**: Extension of DeLP that connects to relational databases as external data sources, translating SQL query results into DeLP facts at argumentation time *(p.0)*.
2. **Formal specification of data integration**: Defines Data Source Retrieval Functions (DSRFs), Predicate Retrieval Functions (PRFs), and Target Connections (TCs) that map database schemas to DeLP predicates *(p.4-5)*.
3. **Dual architecture**: DB-DeLP Server handles SQL-to-DeLP translation; a separate DeLP Server handles the actual argumentation. They communicate via shared predicates *(p.7)*.
4. **Empirical evaluation**: Demonstrates scalability with experiments up to 10,000+ database records, comparing classical vs. dialectical approaches *(p.10-11)*.
5. **Example applications**: Decision Support Systems, Argument-based Recommendation Systems *(p.6)*.

## Methodology

### DeLP Background *(p.2-3)*

DeLP (Defeasible Logic Programming) combines logic programming with defeasible reasoning. Key elements:
- **Strict rules**: `head <- body` (cannot be defeated)
- **Defeasible rules**: `head -< body` (can be defeated by counterarguments)
- **Facts**: ground literals
- A **defeasible derivation** for a literal `h` from a program `(Pi, Delta)` exists when there is a finite sequence of literals ending in `h`, each justified by a strict or defeasible rule
- An **argument** `<A, h>` for a literal `h` is a minimal, non-contradictory set of defeasible rules that can derive `h` together with strict rules and facts *(p.2)*
- Arguments interact via **counterarguments**: `<A1, h1>` counterargues `<A2, h2>` at sub-argument `<A, h>` iff `h` and `h1` disagree *(p.2)*
- **Dialectical trees** evaluate whether an argument is ultimately warranted, considering all attackers, attackers of attackers, etc. *(p.2-3)*

### DB-DeLP Architecture *(p.3-7)*

The framework introduces several formal components:

**Definition 5 (DB-DeLP Program):** `P_DB = (Pi, Delta, Omega_DB)` where `Pi` = strict rules, `Delta` = defeasible rules, `Omega_DB` = set of database declarations linking predicates to external databases *(p.4)*

**Definition 6 (Database Declaration):** `D_i = (db_i, TC_i)` specifying a database `db_i` and a set of Target Connections `TC_i` *(p.4)*

**Definition 7 (Target Connection):** A TC maps a predicate name and parameter list to a database, specifying which fields and tables provide data. For each TC, the system:
1. Identifies data sources (databases, tables, fields)
2. Builds a world data model
3. Creates SQL queries to retrieve relevant data *(p.4)*

**Definition 8 (Data Source Retrieval Function - DSRF):** `dsrf: {D_1, ..., D_n} -> {tc_1, ..., tc_k}` - for a set of database declarations, returns the set of all TCs for a given predicate *(p.5)*

**Definition 9 (Preliminary Retrieval):** Given a set of available databases, this function collects all TCs for a predicate in the program *(p.5)*

**Definition 10 (Persistence Relation):** `PR = {(Cvar -> P(D))}` maps condition variables to sets of database indicators. If data for a predicate persists in a TC, the PR can be used to optimize retrieval *(p.5)*

**Key components of the framework:**

1. **Domain Data Logic (DDL):** Captures the domain of each database - the data sources, their tables, fields, and relationships *(p.6)*
2. **Domain Logic (DL):** Captures the correspondence between domain data and DeLP predicates - what tables/fields map to what predicate parameters *(p.6)*
3. **Translation Layer:** Converts between DeLP predicates and SQL queries. When the argumentation process needs data, it sends the predicate to the DB-DeLP Server, which translates it to SQL, queries the database, and returns DeLP-formatted facts *(p.7)*

### Argumentation Process *(p.7-8)*

Two key algorithms:

**Algorithm 1 (Strict Retrieval Function):** For each strict rule in the program:
1. Select all database declarations matching the predicate
2. Decompose L into predicate name and parameter list
3. For each data source, use DSRF to find the TC, get User/Pass
4. Connect to database, execute SQL query
5. Return facts *(p.7)*

**Algorithm 2 (Presumption Retrieval Function):** Similar to Algorithm 1 but operates on defeasible rules. It collects facts that support the body of defeasible rules *(p.7)*

### Query Processing *(p.8)*

When a query arrives:
1. The DB-DeLP Server receives the query
2. It looks for all strict and defeasible rules relevant to the query
3. For each relevant predicate, it generates SQL queries and retrieves data from databases
4. Retrieved data is translated into DeLP facts
5. These facts are combined with the program's rules
6. The DeLP Server performs the dialectical analysis
7. Results are returned *(p.8)*

## Key Equations

### Argument Structure *(p.2)*
$$\langle \mathcal{A}, h \rangle \text{ where } \mathcal{A} \subseteq \Delta$$
An argument for literal $h$ is a minimal, non-contradictory subset of defeasible rules $\mathcal{A}$ such that $h$ can be defeasibly derived from $\Pi \cup \mathcal{A}$ *(p.2)*

### Running Time Complexity *(p.12)*
$$O\left(\sum_{i=1}^{k} n_i \times \prod_{j=1}^{p_i} s_{ij}\right)$$
where $k$ = number of predicates, $n_i$ = number of entries in the predicate table, $p_i$ = number of parameters of predicate $i$, $s_{ij}$ = number of rows in table $j$ for parameter $j$ of predicate $i$ *(p.12)*

### Variables

| Variable | Meaning | Page |
|----------|---------|------|
| $\Pi$ | Set of strict rules and facts | p.2 |
| $\Delta$ | Set of defeasible rules | p.2 |
| $\Omega_{DB}$ | Set of database declarations | p.4 |
| TC | Target Connection - maps predicate to database schema | p.4 |
| DSRF | Data Source Retrieval Function | p.5 |
| PRF | Predicate Retrieval Function (returns facts from DB) | p.5 |
| PR | Persistence Relation | p.5 |
| DDL | Domain Data Logic | p.6 |
| DL | Domain Logic | p.6 |
| $P_{DB}$ | DB-DeLP program $(Pi, Delta, Omega_{DB})$ | p.4 |

## Parameters Table

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Database records | n | count | - | 100-10,000 | p.10-11 | Tested with MySQL |
| Predicates | k | count | - | 1-7 | p.10-11 | Number of TC predicates |
| SQL execution time | - | ms | - | 1-1,553 | p.11 | Varies with record count |

## Empirical Results *(p.10-12)*

### Experimental Setup
- Operating System: Windows 7 32-bit
- Processor: Intel Core i5 2450 @ 2.50 GHz
- Memory: 1 GB DDR3 1333 MHz
- Database: MySQL
- Implementation languages: Java (DB-DeLP Server), Prolog (DeLP)

### Key Findings

1. **SQL overhead is manageable**: For a simple query with 100 records, total execution was ~93ms; with 10,000 records, ~1,553ms *(p.11, Table 3)*
2. **Classical vs. dialectical approach**: When contradictory information exists, the dialectical approach (building full argument trees) takes considerably longer than the classical approach (just collecting facts), but produces warranted conclusions *(p.11)*
3. **Scalability**: The system scales linearly with number of database records for simple queries. For complex queries with multiple predicates, time grows with the product of table sizes *(p.12)*
4. **Overhead decomposition**: Time splits into SQL query generation, SQL execution, result translation, and DeLP argumentation *(p.11)*

### Performance Tables *(p.11)*

**Table 2** (Simple query, no contradictions):
| Records | Total time (ms) |
|---------|----------------|
| 100 | 93 |
| 1,000 | 359 |
| 10,000 | 1,553 |

**Table 3** (With dialectical process):
| Records | Total time (ms) |
|---------|----------------|
| 100 | 109 |
| 1,000 | 1,045 |
| 10,000 | - |

## Figures of Interest

- **Fig. 1** *(p.4)*: Structure of relevant information for database retrieval - shows the TC structure with predicates table, parameters table, relatedTables table, foreignKeys table
- **Fig. 5** *(p.6)*: A db-dlp for the stock market example
- **Fig. 6** *(p.6)*: The producer-translation database schema
- **Fig. 7** *(p.7)*: The DB-DeLP argumentation process architecture diagram showing DB-DeLP Server, DeLP Server, SQL queries, and Domain Data
- **Fig. 8** *(p.9)*: Two db-dlps showing a complete query processing example with movie/series recommendation
- **Fig. 9** *(p.10)*: The data measured in the IMDB database tables
- **Fig. 10** *(p.10)*: The setup of tables in the producer-translation database
- **Fig. 11** *(p.12)*: Filtering by the producing and measuring of results (performance chart)

## Examples

### Stock Market Example *(p.3-4)*
- Database contains stock information (company, price, sector)
- Strict rule: A stock is risky if the company is in a risky sector
- Defeasible rule: Recommend buying stocks from companies with good prices, unless the company is risky
- DeLP can reason about whether to recommend a stock by building arguments from database facts and defeating counterarguments

### Movie/TV Recommendation Example *(p.8-9)*
- IMDB-like database with movies, actors, genres, user preferences
- The system builds arguments for/against recommending a show
- Example: "Game of Thrones" - arguments for recommendation based on user liking certain actors; counterarguments based on genre preferences *(p.9)*

### Pharmaceutical Example *(p.3)*
- Database with diseases, drugs, treatments
- Defeasible rules encode medical knowledge (e.g., "if patient has disease X, prescribe drug Y unless contraindicated")
- Contradictory conclusions can arise (different drugs for same disease), resolved through dialectical analysis

## Limitations

1. **No caching**: Every query re-retrieves data from databases; no caching mechanism is described *(p.7)*
2. **Single-database assumption per predicate**: While multiple databases can be connected, each TC maps to one database *(p.4-5)*
3. **Performance with complex queries**: The product-of-tables complexity can become expensive with many predicates *(p.12)*
4. **Static rule base**: The strict and defeasible rules are fixed; only facts come from databases *(p.4)*
5. **No distributed argumentation**: The framework assumes a centralized DeLP server *(p.7)*
6. **Limited experimental scope**: Tests use relatively small databases (up to 10,000 records) compared to real-world scale *(p.11)*

## Arguments Against Prior Work

- Prior argumentation systems (e.g., pure DeLP, standard Dung AFs) require all facts in memory, which is infeasible for large-scale applications *(p.0)*
- Simple database wrappers that load all data are not scalable *(p.0)*
- The approach differs from Datalog-based systems in that it maintains the full dialectical semantics of DeLP rather than reducing to Datalog queries *(p.12)*

## Design Rationale

- Separating DB-DeLP Server from DeLP Server allows the argumentation engine to remain unchanged while adding database connectivity *(p.7)*
- Using SQL as the query language for databases allows compatibility with any relational DBMS *(p.5)*
- The TC abstraction layer provides a clean mapping between logical predicates and physical database schemas *(p.4)*

## Testable Properties

1. **TC-predicate mapping is deterministic**: Given a TC specification and a database state, the set of DeLP facts generated is uniquely determined *(p.4-5)*
2. **Argument minimality**: Every argument `<A, h>` must be a minimal set - no proper subset of A can derive h *(p.2)*
3. **Non-contradictory arguments**: No argument can contain both `h` and `~h` *(p.2)*
4. **SQL generation correctness**: For a given predicate with parameters, the generated SQL query must retrieve exactly the tuples matching the TC specification *(p.5)*
5. **Warranted conclusions are stable under data addition**: Adding irrelevant data to the database should not change the warranted status of a conclusion (monotonicity for irrelevant data) *(p.2-3)*
6. **Running time scales as O(sum of products)**: The empirical running time should match the theoretical complexity bound *(p.12)*

## Relevance to propstore

This paper is **moderately relevant** to propstore:

1. **Database-backed argumentation**: propstore's argumentation layer currently operates over in-memory claims. DB-DeLP's approach of connecting argumentation engines to external data sources is directly relevant to scaling propstore to larger knowledge bases. The TC/DSRF pattern could inform how propstore retrieves claims from git-backed storage for argumentation.

2. **Defeasible reasoning over structured data**: propstore already uses ASPIC+ for argumentation. DeLP is a related but different framework. The key insight - that facts for argumentation can be dynamically retrieved from structured storage rather than pre-loaded - applies to propstore's sidecar build process.

3. **Translation layer pattern**: The DDL/DL separation (domain data logic vs. domain logic) mirrors propstore's separation between source storage and the semantic layer. The TC abstraction could inform how propstore maps between its claim storage format and the argumentation engine's input format.

4. **Scalability concerns**: The performance analysis highlights that the main bottleneck is data retrieval, not argumentation itself - relevant to propstore's sidecar rebuild performance.

5. **Limitation**: DB-DeLP uses DeLP rather than ASPIC+, so the specific formal machinery doesn't directly port. However, the architectural pattern (external data source -> translation layer -> argumentation engine) is framework-agnostic.

## Open Questions

1. How would the TC abstraction work with non-relational storage (e.g., propstore's git-backed YAML)?
2. Could the DSRF/PRF pattern be adapted for lazy claim loading in propstore's argumentation layer?
3. What is the performance impact of the dialectical tree construction when databases contain many contradictory entries?
4. How does the framework handle database updates during argumentation?

## Related Work

- **DeLP** (Garcia & Simari 2004) - the base defeasible logic programming system extended here
- **Datalog** - related but different approach to database-logic integration; DB-DeLP preserves full dialectical semantics unlike Datalog reduction
- **ODBC/JDBC** connectivity - standard database connectivity used as transport layer
- **Dung AFs** - the abstract argumentation framework that DeLP's dialectical trees implement a specific instance of
- **ASPIC+** - alternative structured argumentation framework (not discussed in this paper but relevant to propstore)
- **Knowledge-Based Systems with databases** (refs [8], [30]) - prior work on integrating knowledge systems with large databases

## Collection Cross-References

### Already in Collection
- [[Garcia_2004_DefeasibleLogicProgramming]] -- the base DeLP system that DB-DeLP extends with database connectivity
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] -- foundational defeasible reasoning framework by the same research group (Simari is co-author on both)
- [[Dung_1995_AcceptabilityArguments]] -- the abstract argumentation framework whose semantics underpin DeLP's dialectical trees

### New Leads (Not Yet in Collection)
- Chesnevar, Maguitman & Loui (2000) -- "Logical models of argument" ACM Computing Surveys -- survey of argument models
- Stolzenburg et al. (2003) -- "Computing generalized specificity" -- used for DeLP's comparison criterion
- Besnard & Hunter (2008) -- "Elements of Argumentation" MIT Press -- comprehensive textbook

### Cited By (in Collection)
- [[Cyras_2021_ArgumentativeXAISurvey]] -- cites this as an example of argumentation over structured data sources

### Conceptual Links (not citation-based)
- [[Diller_2025_GroundingRule-BasedArgumentationDatalog]] -- directly related: grounding argumentation in Datalog, which is the alternative approach to DB-DeLP's SQL-based data retrieval for argumentation
- [[Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible]] -- related pattern of connecting an external system (LLM) to a structured argumentation framework (ASPIC+), analogous to DB-DeLP connecting databases to DeLP
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] -- ASPIC+ is the main alternative structured argumentation framework to DeLP; both build arguments from rules and facts but with different formal machinery
