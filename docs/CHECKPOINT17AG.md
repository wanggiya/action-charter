# Checkpoint 17AG — idempotent recipe-storage resume

Checkpoint 17AG corrects the Planner-derived recipe save transition when the
same canonical recipe was already stored by an earlier attempt.

After reverifying the immutable plan and approval evidence, recompiling the
recipe, rerunning deterministic policy, and comparing the reviewed digest, the
server now treats an existing canonical recipe as a successful resume only when
the stored artifact validates to the exact same digest. It does not rewrite or
modify the file. A mismatched, invalid, or unsafe artifact still fails closed.

Save failures are displayed beside the Planner recipe controls as a prominent
`RECIPE NOT STORED` result rather than appearing under the unrelated execution
envelope preview.
