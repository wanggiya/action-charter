# WSL frontend setup

## Diagnose the CMD.EXE / UNC-path error

Run these commands in Ubuntu WSL from the repository:

```bash
type -a node npm pnpm
command -v node
command -v pnpm
```

If `node` or `pnpm` resolves under `/mnt/c/`, ends in `.exe` or `.cmd`, or
launches `CMD.EXE`, WSL is borrowing the Windows installation. A Windows
package-manager shim cannot reliably use the WSL UNC working directory, which
causes the `C:\Windows\_tmp...` error. Changing repository permissions or
running the command with `sudo` does not correct that environment mismatch.

## Install a Linux-local toolchain

Install nvm inside WSL by following the current command in the official
[`nvm-sh/nvm` README](https://github.com/nvm-sh/nvm#installing-and-updating).
Then open a new WSL shell and run:

```bash
cd ~/projects/geoagent-skill-harness/interface
nvm install
nvm use
corepack enable
corepack prepare pnpm@10.17.1 --activate
hash -r
```

Verify the boundary before installing project packages:

```bash
command -v node
command -v pnpm
node --version
pnpm --version
```

Both paths should be Linux paths, normally beneath `~/.nvm/`; Node should be
22.x and pnpm should be 10.17.1. Then install and validate:

```bash
pnpm install --frozen-lockfile
pnpm build
pnpm dev
```

Do not use the Windows `pnpm.cmd` from WSL and do not use `sudo pnpm install`.
The checked-in `.nvmrc` and `packageManager` field preserve the intended
versions for contributors.
