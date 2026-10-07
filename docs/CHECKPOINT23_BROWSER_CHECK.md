# Checkpoint 23 deterministic browser regression

`scripts/checkpoint23_browser_check.mjs` opens the built production interface in headless Chromium on an ephemeral loopback port. Every API response is an explicit fixture, unrecognized API requests fail, and external requests are blocked. It never calls the live API, model, PostGIS or GeoServer. It exercises rendering/interactions; backend authority/export tests remain separate.

The browser test checks:

- Snakemake choices lead the result list but scroll away, while search/× stay pinned.
- Searching “snake make” finds both supported operations.
- Pointer-following drag, position/viewport preservation on release and stable edited-plan dragging.
- Vertical dragging and Escape cancellation.
- Left-aligned headings, narrative and labels; right-aligned operation names, values and gates in paired rows.
- Geometric right-edge alignment within 1.5 pixels of the card content edge, exposing the legacy `dd max-width:58%` defect.
- Original path casing, larger bold authorization duration and same-row Authorize/Execute.
- Execute does not submit the authorization form, and successful authorization keeps its action row in view.
- Outline and both solid text colors preserve the mixed layout.
- Narrow review layout and refresh/history recovery without operation reexecution.
- No page errors and zero live GIS calls.

## Run

Run `make interface-validate` first. Provide an installed Playwright module through `ACTIONCHARTER_PLAYWRIGHT_MODULE`, or install its test-only package outside the repository. The validation session used Playwright 1.63.0 and its Chromium browser in `/tmp`. No dependency was added to the application.

Example after preparing a temporary installation/browser:

```bash
export ACTIONCHARTER_PLAYWRIGHT_MODULE=/tmp/actioncharter-ui-review/node_modules/playwright/index.mjs
export PLAYWRIGHT_BROWSERS_PATH=/tmp/actioncharter-browser-cache
export ACTIONCHARTER_BROWSER_RESULTS=/tmp/actioncharter-ui-review/results
node scripts/checkpoint23_browser_check.mjs
```

Chromium needs its runtime libraries. This session extracted the missing audio library locally under `/tmp/actioncharter-browser-libs/runtime`; no system package was installed. If using that setup, add its `usr/lib/x86_64-linux-gnu` directory to `LD_LIBRARY_PATH` for this command. Loopback/browser execution may require sandbox permission.

The output includes RESULTS.json and authorization/Outcome/narrow screenshots. Prior failures remain separate evidence; they are not the latest result. Screenshots contain public fixture data and a clearly labeled fake model. Do not treat this as a live-model or database acceptance run, or as a frame-rate guarantee on the operator's machine.
