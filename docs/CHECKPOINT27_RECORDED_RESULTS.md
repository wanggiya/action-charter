# Checkpoint 27.4a — recorded operation results

Current presentation update: [27.4c Results workspace](CHECKPOINT27_RESULTS_WORKSPACE.md) supersedes nested Outcome cards with operation-selected result tabs; recorded scope and evidence boundaries below remain unchanged.

Delivered 2026-10-18. This is the recorded-result slice of
[the ordered delivery plan](POST_CALCULATION_DELIVERY_PLAN.md), not completion of
checkpoint 27, learning-policy work or generated-code capability acquisition.

## Delivered behavior

Select an operation in the current chat workflow or Workflow operations list.
The information panel shows its purpose, proposed/recorded status, readable
calculation formula, compact input → output references and expandable full paths
and dependency order. Recorded results include run identity/time, bounded table
rows and named validation checks. Calculation previews start with referenced
source columns and derived columns; Show all columns exposes the saved table.
Raw arguments, hashes, result JSON and validation JSON stay under Technical details.

Outcome and durable Workflow runs use the same recorded-result card. Execution
History → Workflow runs → select a run → expand a step → View in information
panel explicitly selects that run when its chat and plan match the current graph.
Other runs remain inspectable within history, without attaching their success to
the graph. Legacy inspection-history selections are labelled separately. The
existing direct Snakemake export route keeps its immediate result display; old
inspection/export records without a persisted chat link require explicit history
selection after refresh and are not automatically assigned to a chat.

Opening a chat/refresh reads the newest matching record from the recent inventory
(up to 50 runs). Both plan digest and conversation ID must match. Missing,
unlinked or unreadable evidence is labelled, not replaced with another chat's
result. Pending edits remove execution evidence until a matching validated plan
is selected. Late responses from an earlier scope are ignored; history selection
also guards out-of-order reads. A delayed default runtime projection can no longer
replace an already restored chat workflow. Critic commentary follows the selected
run rather than a different current attempt. Opening results never regenerates a plan, calls a
model, grants permission or repeats execution.

The Write tools disclosure reports the API's current configuration and shows the
existing launcher flag when disabled. Configuration is separate from exact
workflow authorization; no runtime permission switch is introduced.

## Preview and evidence limits

New CSV transform results save at most 10 rows, still within the existing 4 KiB
row-preview budget and 160-character cell projection. Inspection keeps its typed
preview_rows limit/default. All services, interface and CLI consume the same
backend result. Historical records retain their original saved previews. Wider
results may save fewer rows or omit the intermediate preview under the existing
6 KiB result / 3 KiB validation budgets. Counts and missing-value markers are
shown honestly; this panel does not reread or revalidate current files.

Validation reports recorded checks, including Calculated values verified,
source/output identity, counts and columns. These checks establish bounded
operation correctness at execution time, not suitability of a domain formula or
continued validity of files/database targets after that run. Failure/cancellation
states and any present values are marked as potentially partial. Recovery still
requires the existing fresh-target/fresh-authority process.

Maps/charts, broad actual-model evaluation, domain recall, new executable adapters
and optional reward-based selection remain later gates. No live database/service
writes or new model acceptance are implied by fixture browser tests.

## Operator acceptance

1. Stop the existing launcher with Ctrl+C, then use
   `bash scripts/start_actioncharter.sh --enable-write-tools`. Keep that terminal
   running and open http://127.0.0.1:5173. Normal ports remain 5173/8765.
2. In a new Planner chat, request: “Inspect sample_orders.csv. Create a new numeric
   column doubled equal to amount multiplied by 2. Preserve all original columns
   and propagate missing values. Save to a fresh CSV. Do not execute yet.”
3. Check that the workflow actually includes Inspect CSV table and Calculate table
   columns. Select Calculate: the formula must read doubled = (amount × 2), with a
   fresh output path under Full paths and order. Before execution it must say Not
   executed and show no recorded result table. Resolve planning errors before
   continuing; a model response alone does not establish a correct workflow.
4. Authorize the exact write scope, then Execute once. Select Calculate and inspect
   its information panel: six sample rows should show doubled values 20, 40,
   missing, 80, 10, 60 (numeric display may include .0). Calculated values verified
   and the source/output/count/column checks must pass. Show all columns must retain
   order_id values such as 001. Inspection selection must not claim calculation
   validation. These checks require a new record for the expanded six-row preview;
   older records can legitimately contain only five rows.
5. Refresh the browser and reopen the same chat. Select Calculate: formula, path,
   run identity and saved values must restore without Execute. Inspect that run in
   Execution History → Workflow runs and use View in information panel on its step.
6. Edit the formula through Block tools → Parameters: draft results must disappear.
   Do not execute this draft just to test presentation. Switch to a separate chat:
   the former chat's evidence must not appear as its result. Reopen the original
   chat to inspect the original evidence again.

## Automated acceptance

`make test` covers shared backend behavior, including known calculation values,
independent validation and authority/failure bounds. `make interface-validate`
checks frontend types/build. The calculation browser journey uses the actual API,
temporary CSV files and deterministic model replies; it checks previews,
inspection/calculation selection, refresh, explicit history selection, wrong-chat
exclusion and draft isolation. The recipe/runs browser journey covers cancellation,
recovery, combined spatial-attribute/CSV composition and API restart restoration.
Verified: 1,769 backend tests, frontend types/build (existing bundle-size advisory),
12 calculation browser cases and six recipe/runs browser cases; nine additional
intercepted-API UI cases cover direct Snakemake export, paired authorization
alignment, materials, drag and legacy-history restoration. The strengthened
known-answer backend calculation test also passed in its 37-test module. No live
model or database/service writes were performed for this slice.

Project-local browser binaries/libraries and temporary profiles remain isolated
from ordinary browser caches. See package scripts for repeatable commands.
