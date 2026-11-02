# Checkpoint 16A — Bounded GeoServer Inspection

Checkpoint 16A establishes read-only observation before ActionCharter receives
any GeoServer publication authority. It inspects one exact allowlisted
workspace, datastore, feature type, and published layer through fixed REST GET
paths.

It cannot accept an arbitrary URL, REST path, HTTP method, request body, style
change, publication, update, or deletion operation.

## Local Docker configuration

Attach the existing GeoServer container and `mcp-gis` to the same external
Docker network. Add only non-secret values to `.env`. Values in this file are
also interpolated into Compose, so the configured URL must use the GeoServer
container name rather than `localhost`:

```dotenv
GEOSERVER_BASE_URL=http://geoserver:8080/geoserver
GEOSERVER_USER=geoagent
GEOSERVER_PASSWORD_FILE=.secrets/geoserver_password
ALLOWED_GEOSERVER_WORKSPACES=geoagent_test
ALLOWED_GEOSERVER_DATASTORES=postgis
```

Replace the workspace and datastore values with their exact GeoServer catalog
names. A GeoServer workspace is not a PostgreSQL schema: for the current local
prototype, `geoagent_test` is the GeoServer workspace while `agent_sandbox` is
the schema selected in the PostGIS datastore.

The reference Docker setup uses these separate boundaries:

| Boundary | Local prototype value |
|---|---|
| GeoServer user | `geoagent` |
| GeoServer role | dedicated workspace role, such as `ROLE_GEOAGENT` |
| GeoServer workspace | `geoagent_test` |
| GeoServer datastore | `actioncharter_postgis` |
| PostgreSQL database | `geoagent` |
| PostgreSQL schema | `agent_sandbox` |

Create the workspace and datastore as a GeoServer administrator. Configure the
datastore for host `postgis`, database `geoagent`, schema `agent_sandbox`, and
the separately managed PostgreSQL credential. Grant the dedicated GeoServer
role read and workspace-admin access only to `geoagent_test`; do not grant the
user global `ROLE_ADMINISTRATOR`.

GeoServer's default `security/rest.properties` may restrict every REST method
to global administrators. Retain its global restrictions and add only the two
GET rules required for the dedicated workspace, substituting the exact role:

```properties
/rest/workspaces/geoagent_test*;GET=ROLE_GEOAGENT,ROLE_ADMINISTRATOR
/rest/workspaces/geoagent_test/**;GET=ROLE_GEOAGENT,ROLE_ADMINISTRATOR
/**;GET,HEAD,OPTIONS=ROLE_ADMINISTRATOR
/**;POST,DELETE,PUT=ROLE_ADMINISTRATOR
```

The first rule covers the workspace JSON resource and the second covers its
datastores, feature types, and layers. Do not grant the workspace role GET
access to `/rest/**` globally.

Store the password separately and never commit it:

```bash
mkdir -p .secrets
chmod 700 .secrets
printf '%s' '<password>' > .secrets/geoserver_password
chmod 600 .secrets/geoserver_password
```

The `mcp-gis` image is built with numeric `GEOAGENT_HOST_UID` and
`GEOAGENT_HOST_GID`, so its non-root process can read owner-only Compose secret
files without making them group- or world-readable. Numeric identity avoids
collisions with users or groups already supplied by the GDAL base image.

Prefer a dedicated GeoServer identity whose REST permissions are limited to
the required read operations. Do not place the password in `.env`, a CLI
argument, a plan, or an evidence file.

For a CLI running directly in WSL instead of in Compose, export the
configuration and override only the URL with the host-published endpoint:

```bash
set -a
. ./.env
set +a
```

Then inspect one exact target:

```bash
GEOSERVER_BASE_URL=http://localhost:8080/geoserver \
  .venv/bin/geoagent inspect-geoserver-layer \
  --workspace geoagent_test \
  --datastore actioncharter_postgis \
  --layer checkpoint3e_sample_points \
  --pretty
```

Keep the Docker-network URL in `.env`. Apply the host URL only to the individual
WSL command. An exported shell variable has higher precedence than Compose's
`.env` value and can otherwise cause containers to receive `localhost`.
For `mcp-gis` in Compose, retain
`GEOSERVER_BASE_URL=http://geoserver:8080/geoserver`; `localhost` inside that
container would refer to `mcp-gis` itself.

Connect the separately managed `geoserver` and `postgis` containers to the
external `geoagent-backend` network. The `mcp-gis` service joins that network
through Compose. Verify the container-side path with:

```bash
docker compose --profile tools run --rm \
  --entrypoint geoagent \
  mcp-gis \
  inspect-geoserver-layer \
  --workspace geoagent_test \
  --datastore actioncharter_postgis \
  --layer checkpoint3e_sample_points \
  --pretty
```

Exit codes are:

- `0`: the exact feature type or published layer was inspected;
- `1`: the bounded workspace, datastore, feature type, or layer was not found;
- `2`: configuration, policy, authentication, transport, or response evidence
  was invalid or unavailable.

## Deferred integration

The local CLI is the first integration target. The Compose service receives
the same read-only operation through MCP, but remote GeoServer access,
publication credentials, multi-host configuration, and every write operation
remain later Checkpoint 16 increments.
