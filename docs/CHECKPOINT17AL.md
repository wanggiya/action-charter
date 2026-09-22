# Checkpoint 17AL — clean local development lifecycle

Checkpoint 17AL makes deliberate `Ctrl+C` shutdown of the source-pinned
interface API quiet and explicit. `KeyboardInterrupt` is handled at the
launcher boundary after the HTTP server closes its socket.

Troubleshooting guidance now distinguishes Vite hot reload, full page reload,
and ordinary React state changes, and clarifies that workflow API operations do
not modify interface source code.
