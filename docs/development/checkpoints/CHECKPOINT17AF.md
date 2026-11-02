# Checkpoint 17AF — exact stored-recipe approval handoff

Checkpoint 17AF removes the manual rediscovery gap after a Planner-derived
recipe is stored.

The **Review recipe approval scope** action carries the exact stored recipe
SHA-256 into a freshly loaded saved-recipe inventory. The matching artifact is
moved to the top regardless of the selected temporal or alphabetical ordering,
and the interface identifies it as the newly stored recipe.

The transition remains non-authoritative: it does not prepare an approval
request, record a decision, verify approval, preview execution, or execute a
skill. The operator must still review the stored recipe card and explicitly
select **Prepare approval request**.

## Validation

Complete the 17AE Planner-to-recipe flow through immutable storage. Select
**Review recipe approval scope** and confirm that the matching recipe digest is
first in the inventory and that the interface reports it selected. Change the
sort order and repeat the handoff; the exact transition target must remain
first. Confirm no approval request exists until **Prepare approval request** is
selected.
