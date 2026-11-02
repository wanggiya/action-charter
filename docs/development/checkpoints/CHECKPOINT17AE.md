# Checkpoint 17AE — reviewed Planner recipe storage

Checkpoint 17AE turns a compiled Planner recipe candidate into an explicitly
reviewed, immutable stored recipe without transferring or expanding authority.

The interface requires confirmation of the exact recipe digest and ordered
steps. The server then reloads the immutable plan and approval evidence,
independently verifies that authority again, recompiles the recipe, reruns
deterministic recipe policy, and compares the resulting digest before writing
under the fixed workflow-recipe root.

The stored recipe is **not approved and not executed**. Select **Open saved
recipes** to enter the existing recipe approval, verification, preview, and
execution sequence. The prior plan approval remains evidence for compilation;
it is not accepted as recipe execution approval.

The compilation control was also redesigned as a full-width transition card
with clear primary and secondary labels and distinct compiled, reviewed, and
stored states.
