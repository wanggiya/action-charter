# Core concepts: skill, recipe, workflow, and template

ActionCharter separates reusable capability from reusable orchestration and
from an individual execution record. Keeping these concepts distinct is
necessary for correct policy, approval, validation and evidence.

## Skill

A **skill** is one bounded professional capability. It has a typed input/output
contract, implementation or adapter, policy checks, and tests. Examples include
`inspect_vector`, `convert_raster`, `load_vector_to_postgis` and
`validate_postgis_layer`.

A skill is not a complete workflow and does not receive authority merely by
being visible in the interface. Generated candidate skills must still pass the
Builder testing, review, promotion and activation lifecycle.

## Recipe

A **recipe** is a reusable, parameterized graph of trusted skill steps and
dependencies. It specifies how known capabilities can be composed, but it does
not by itself mean that a particular operation has been approved or executed.

The trusted template catalog in `context/RECIPE_TEMPLATES.yaml` contains
reviewed starting definitions. Interface templates are views of these recipes,
not a separate catalog.

## Workflow

A **workflow** is one concrete lifecycle instance. It begins with an operator
request and specific inputs, then accumulates proposal, deterministic policy,
plan digest, approval, execution state, validation, independent verification,
evidence and release information as applicable.

Two workflows can use the same recipe while having different names, input
files, parameters, approvals, timestamps, outcomes and evidence identities.

## Template

A **template** is a trusted recipe offered as a convenient starting point. It
reduces repeated configuration; it does not bypass proposal validation,
compilation, policy, approval or execution controls.

## CLI/interface equivalence testing

Before the guided interface is considered operationally complete, each major
capability should be exercised through both surfaces:

1. create or select a skill, recipe or workflow using the CLI;
2. complete the governed CLI lifecycle and retain its safe evidence;
3. create a comparable case through the interface using different identifiers
   and non-conflicting output targets;
4. compare normalized plans, steps, policy findings, approval requirements,
   validation results and evidence structure;
5. require equivalent authority boundaries and fail-closed behavior;
6. never compare by reusing a destructive target or by assuming byte-identical
   timestamps, generated identifiers or digests.

The purpose is contract and governance equivalence, not merely that both paths
produce a file. Until an interface action has such coverage, the CLI remains
the authoritative operational path for that action.
