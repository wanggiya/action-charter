# Acquire and reuse a CSV text-normalization adapter

Synthetic data; no database/service access. Copy `orders.csv` into `data/input`
under a fresh name such as `normalization_orders.csv`.

In a new Planner chat, turn **Acquire capabilities · optional** ON and send:

> Inspect normalization_orders.csv. Trim whitespace and uppercase region into a
> new region_clean column, preserve all original columns, and save a fresh CSV.
> Do not execute.

If no compatible operation is installed, review the strip → upper definition,
synthetic/held-out checks and Critic status. **Install and update workflow**
registers the exact package and requests a normal workflow; it does not run it.
Review the resulting inspection and text adapter, enable writes, Authorize and
Execute separately. Expected `region_clean`: NORTH, SOUTH, missing; original
order IDs 001/002/003, row count and columns are preserved.

A new chat defaults acquisition OFF. Ask for the same transformation on another
compatible CSV; Planner should reuse the installed operation without generating
another candidate. Installed definitions are project-visible; private transcripts
and attempt receipts are not shared between chats. No model reliability claim is
established by this example. [Bounds and acceptance](../../docs/CHECKPOINT28_1.md).
