# Checkpoint 17AI — source-pinned interface API development

Checkpoint 17AI adds `scripts/serve_interface_dev.sh`, which starts the local
interface API from the current checkout's `src` tree and prints the imported
module path and route count before listening. This prevents a stale installed
package or unexpected working directory from silently serving older routes.

Malformed POST bodies now report `request payload is invalid` rather than the
misleading endpoint-independent `recipe proposal is invalid` message.

Operational guidance in `INTERFACE_API_TROUBLESHOOTING.md` distinguishes CPU
time from elapsed runtime, shows how to identify the exact listener PID and
working directory, and defines the expected empty-body route probe.
