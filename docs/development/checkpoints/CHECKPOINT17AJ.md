# Checkpoint 17AJ — visible Planner-to-recipe workspace transition

Checkpoint 17AJ corrects the post-storage transition from the Planner workspace
to saved recipes. The action previously opened the recipe workspace while
leaving the later-rendered Planner overlay open above it, making the click look
inactive even though recipe inventory loading had started behind the panel.

Opening saved recipes now closes the Planner, template, and execution-inventory
overlays before displaying the recipe workspace. It retains the exact preferred
recipe SHA-256 and performs no automatic approval preparation or execution.
