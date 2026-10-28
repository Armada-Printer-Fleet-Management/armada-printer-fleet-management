# `infra/deploy/` — deployment to on-premise hosts

The stack every deployed machine runs: testing, staging and every user installation alike. They
differ only in their environment file.

| File | What it is |
|---|---|
| `compose.yaml` | The six services: `web` (Caddy plus the built frontend), `server`, `db` (Postgres), `garage-s3-storage` (S3 file storage), `keycloak` (identity provider) and `keycloak-db` (Keycloak's own Postgres). Images are pulled, never built here |
| `Caddyfile` | Baked into the web image. Serves the frontend, forwards `/api` to the server and Keycloak's sign-in paths under `/auth` to Keycloak, and obtains HTTPS certificates for `DOMAIN` |
| `garage.toml` | Garage's configuration, mounted into its container. Single node, sqlite metadata, no replication |
| `armada-realm.json` | Keycloak's `armada` realm: the web client and the roles, with no users. Imported on Keycloak's first start only |
| `install.sh` | Sets up a machine once, then hands over to `armada` |
| `armada` | The command an operator uses for everything after installing: updates, rollback, status, settings |
| `systemd/` | The timer that runs `armada check-for-updates --scheduled` |
| `release.sh` | Assembles a release's files, `VERSION` and `SHA256SUMS`, for either channel; used by the workflows and the tests |
| `release.Dockerfile` | Packs a preview build's release files into its private release image |

Only ports 80 and 443 are published to the network. Both Postgres databases and Garage are
reachable from the other containers and nowhere else. Through Caddy, Keycloak serves only what
users need to sign in, `/auth/realms/armada/` and `/auth/resources/`; its admin console is on
`127.0.0.1:8080`, reachable from the machine itself only.

**Never run `docker compose down -v`** on a deployed machine. It deletes the database, the stored
files, every Keycloak account and Caddy's certificates; re-requesting certificates repeatedly can hit Let's Encrypt's rate
limits.

## How images are published

Images are built once and then promoted: moving a site to a new environment moves a pointer to
an image that already exists, and never rebuilds it. There are three pointers, one per
environment: `:testing`, `:staging` and `:production`.

### Two channels, five packages

Testing and staging builds are unstable and stay private; production versions are public. GHCR
sets visibility per package, never per tag, so the two live in different packages:

| Channel | Tracks | Packages | Visibility |
|---|---|---|---|
| Preview | testing, staging | `armada-server-preview`, `armada-web-preview`, `armada-release-preview` | private |
| Release | production | `armada-server`, `armada-web` | public |

Only staging to production writes to the public packages. **Making a package public cannot be
undone**, and everything ever pushed to it becomes pullable, so nothing unstable may be pushed or
tagged there, even briefly.

A preview build's release files (installer, `armada`, `compose.yaml`, `garage.toml`,
`armada-realm.json`, the timer)
travel in its `armada-release-preview` image, because a GitHub release cannot be private.
Production's are attached to its GitHub release.

### Building: `.github/workflows/deploy.yml`

Runs on every push to `main` or to a `release/*` branch. It builds and starts this stack exactly as
below, checks that Caddy serves the site and `/api/health_check`, and only then pushes
`ghcr.io/<owner>/armada-server-preview`, `armada-web-preview` and the build's release image,
`armada-release-preview`:

| Pushed to | Images tagged with | Pointer moved |
|---|---|---|
| `main` | `sha-` and the first 12 characters of the commit they were built from | `:testing` |
| `release/X.Y.Z` (a hot fix) | the next release candidate, `X.Y.Z-rc.N` | `:staging` |

A commit whose images already exist in the registry is not built again. A manual run from the
Actions tab can be a dry run that pushes nothing.

### Promoting: `.github/workflows/release.yml`

Run by hand, once the team decides a build is ready to move on. It never builds anything: it
gives images that already exist a new name and moves a pointer to them. It has two steps:

1. **Testing to staging.** The build on `:testing` becomes a release candidate: its three preview
   images are tagged `X.Y.Z-rc.N`, `:staging` is moved to them, and a `vX.Y.Z-rc.N` git tag is
   added to the commit they were built from. Candidates get no GitHub release: releases are
   public, and a candidate is unstable.
2. **Staging to production.** The candidate on `:staging` gets its plain version: its server and
   web images are copied, unchanged, into the public packages as `X.Y.Z` and `:production`, a
   `vX.Y.Z` git tag is added to the same commit, the `release/X.Y.Z` branch is created from it,
   and the GitHub release is published with the image digests and the release files that commit's
   `release.sh` makes, installer included. It is marked as the latest release, which is what
   production machines follow.

Only production versions are plain `X.Y.Z`, so they go up only when the team decides they
should. A candidate that fails or is replaced on staging uses up a candidate number, never a
version.

#### Running it

In the repository's **Actions** tab, choose **Release** in the list of workflows, then **Run
workflow**, and fill in:

| Input | What to enter |
|---|---|
| Step | `testing-to-staging` or `staging-to-production` |
| Version | Testing to staging only: the version this build will become, such as `1.3.0`. Ignored for staging to production |
| Dry run | Tick it to see what would happen without changing anything |

The run appears in the list named after the step and version. Its summary page says what was
promoted, under which name, from which commit, and the image digests.

**Do a dry run first.** It runs every check a real run does and shows the result, including the
version in production and every change since it, which is what the version is chosen from.
Then run it again without the tick.

#### Choosing the version

Enter the version this build will become once it reaches production. It must be `X.Y.Z` with
nothing else (`1.3.0`, not `v1.3.0` or `1.3`), and newer than the version in production. Choose
it from the changes since production, which the dry run lists, the same way as the commit
types say:

| Changes since production include | Raise | From `1.2.0` |
|---|---|---|
| a breaking change (`type!:` or a `BREAKING CHANGE:` footer) | major | `2.0.0` |
| a new feature (`feat`) | minor | `1.3.0` |
| only fixes and other changes | patch | `1.2.1` |

#### How the candidate number is chosen

The number is one more than the highest `vX.Y.Z-rc.N` git tag of the version you enter, whoever
made it. Entering the same version again continues its numbers, and a new version starts at 1:

| You enter | Candidates already tagged | The build becomes |
|---|---|---|
| `1.3.0` | none | `1.3.0-rc.1` |
| `1.3.0` | `1.3.0-rc.1` | `1.3.0-rc.2` |
| `1.4.0` | `1.3.0-rc.1`, `1.3.0-rc.2` | `1.4.0-rc.1` |

Promoting a build that is already a candidate of that version is refused: merge a change to
`main` first, so there is a new build on `:testing`. Staging to production needs no input; it
takes the version from the candidate's own tag, so `1.3.0-rc.2` ships as `1.3.0`.

#### Finding the current versions

- **The Releases page** of the repository. The release marked **Latest** is the version in
  production. Only production versions are listed there.
- **The `armada-server-preview` package** on GitHub, under the organisation's **Packages**. Its
  tags show every build and candidate, and which one `:testing` and `:staging` are on. It is
  private, so it is visible only to people with access.
- **Git**, from any clone. Plain `vX.Y.Z` tags are production versions, and `-rc.N` tags are
  candidates:

  ```
  git fetch --tags
  git tag --list 'v*' --sort=-v:refname
  ```

- **A dry run** of the promotion you are about to do: its summary names the version in production
  and what the build would become.

#### When a run refuses

| Message | Why |
|---|---|
| Nothing is on `:testing` (or `:staging`) yet | Nothing has been built or promoted there yet |
| The images on `:testing` do not record a commit | The images were built before `deploy.yml` recorded the commit; merge a change to `main` |
| Enter the version this build is meant to become | The version is empty or not `X.Y.Z` |
| `X.Y.Z` must be newer than the version in production | Choose a higher version |
| The images on `:testing` are already `X.Y.Z-rc.N` | That build is already a candidate of that version |
| The images on `:staging` are not a release candidate | Staging holds something that never went through testing to staging |
| `X.Y.Z` is already released | That candidate's version has shipped already |

Release branches exist for versions that reached production, and the last five are kept. The
one exception is a hot fix's branch, which is created by hand before its version ships; how a
hot fix reaches production is in `docs/git-hygiene.html`.

A machine learns which version its track names from the `VERSION` file in the release files: in
the release image on its pointer for testing and staging, and in the latest GitHub release for
production.

## Installing on a machine

The machine needs Linux with systemd, and Docker Engine with the Compose plugin. There is one
`install.sh`; `release.sh` stamps each copy with its channel, so a GitHub release's copy installs
only production and the release image's copy only testing or staging.

### Production

Download the installer from a release and run it as root; it asks for the domain, an
administrator email and the update policy:

```
curl -fsSLO https://github.com/<owner>/<repository>/releases/latest/download/install.sh
sudo bash install.sh
```

To check the file before running it, download `SHA256SUMS` from the same release too:

```
curl -fsSLO https://github.com/<owner>/<repository>/releases/latest/download/SHA256SUMS
sha256sum --ignore-missing -c SHA256SUMS
less install.sh
sudo bash install.sh
```

`latest` is the newest version promoted to production. Use `releases/download/v<X.Y.Z>/` for a
particular version.

Every question can be answered with a flag instead, and `--non-interactive` turns a missing answer
into an error, for automated setups.

### Testing and staging

These pull from the private preview packages, so the machine logs in to GHCR once, as a bot
account that can only read them:

1. Create a GitHub account for the machines, and a classic personal access token for it with only
   the `read:packages` scope.
2. In each of the three preview packages' **Package settings → Manage access**, give that account
   read access.
3. On the machine, log in once. Docker keeps the login in `/root/.docker/config.json`, which the
   installer, `armada` and the update timer all use; none of them handles the token:

   ```
   sudo docker login ghcr.io -u <bot account>
   ```

4. Read the installer out of the release image on the track's pointer, and run it. `--track`
   defaults to `testing`:

   ```
   sudo docker pull ghcr.io/<owner>/armada-release-preview:testing
   id=$(sudo docker create ghcr.io/<owner>/armada-release-preview:testing none)
   sudo docker cp "$id:/release/." ./armada-release && sudo docker rm "$id"
   sudo bash armada-release/install.sh --track testing --update-policy auto --update-interval 5min
   ```

The image has no shell; `none` is a placeholder command, since it is only created to be copied
from, never started. If the login has expired or lacks access, the installer and the update
check both say so.

The installer generates every password; nobody types or sees one. It writes them only when
`/opt/armada/.env` is new, so running it again on an installed machine keeps them, and keeps its
track unless `--track` says otherwise.

A machine installed before Keycloak was added has no Keycloak passwords, and updating it fails.
Remove it with `armada uninstall --delete-data`, which deletes its data and `.env`, then install
again.

## Running a machine: the `armada` command

| Command | What it does |
|---|---|
| `armada status` | The version, whether every service is healthy, update settings, disk use, certificate expiry |
| `armada update <version\|latest>` | Moves to a version. If it does not become healthy within three minutes, the previous version is put back |
| `armada rollback [version] [--yes]` | Asks, then returns to the version before the last update, with the same health check. Running it again undoes the rollback; to go further back, name a version. `--yes` skips the question |
| `armada check-for-updates` | Says whether a newer version is available on this machine's track |
| `armada logs [service] [lines]` | Follows the logs |
| `armada restart`, `stop`, `start` | Restarts, stops or starts every service; data is kept |
| `armada reconfigure` | Asks the installation questions again |
| `armada config <key> [value]` | Shows or changes one setting (below) |
| `armada uninstall [--delete-data]` | Removes Armada. Without `--delete-data`, the data and `/opt/armada/.env` stay, so installing again finds them |

| Setting | Values |
|---|---|
| `domain`, `admin-email` | As asked by the installer; changing the domain gets a new certificate |
| `track` | Which pointer the machine follows: `production` for every real installation; `staging` and `testing` for ours. A machine moves between testing and staging freely, but to or from production only by reinstalling from the other channel |
| `update-policy` | `notify` (the default) records that a version is available, `auto` installs it, `off` never checks |
| `update-window` | For `auto`: only install between these times, e.g. `02:00-05:00`. Empty means any time |
| `update-interval` | How often the timer checks, e.g. `6h` (the default) or `5min` |

A machine follows its pointer down as well as up: if a pointer is moved back, automatic updates
move back with it.

On the machine: settings and generated passwords are in `/opt/armada/.env` (readable by root
only), each installed version's files are in `/opt/armada/releases/`, and the timer is
`armada-update.timer`.

`.github/workflows/deploy.ci.yml` lints these scripts with shellcheck and, against a local
registry, runs a whole install, update, rollback, failed update, uninstall and reinstall through
the preview channel, then a production install and update through the release channel, on every
pull request that changes them.

### Keycloak's admin console

The site refuses Keycloak's admin console and `master` realm, so reach them from your own
computer through an SSH tunnel to the machine:

```
ssh -L 8080:localhost:8080 <user>@<machine>
```

Then browse to `http://localhost:8080/auth/admin` and sign in with `KEYCLOAK_ADMIN_USERNAME` and
`KEYCLOAK_ADMIN_PASSWORD` from `/opt/armada/.env`. Keycloak reads that password only on its first
start, so change it in the console after that, not in `.env`. On the machine itself, Keycloak's
command-line admin tool needs no tunnel:
`docker exec -it armada-keycloak-1 /opt/keycloak/bin/kcadm.sh`.

The realm file is also read only on first start, so a later change to it does not reach a
machine that already has the realm.

## Running it locally

`python scripts/compose_run.py deploy` builds both deploy images locally, tags them with the
names `compose.yaml` expects, and starts the stack. Settings, including
generated secrets, are in `config/compose.deploy.env`; see `config/compose.deploy.example.env`.
For local testing, `--domain :80` serves plain HTTP with no certificate, so the admin email is
not used and any address works. A real domain gets an HTTPS certificate, and the email becomes
its expiry contact.

```
python scripts/compose_run.py deploy --domain :80 --admin-email admin@localhost
python scripts/compose_run.py deploy down
```

`--domain :80` serves plain HTTP, for a test machine without DNS. A real domain that resolves to
the machine gets an HTTPS certificate automatically.

**Belongs here:** the generic mechanism: how a release is installed, started and upgraded.

**Does not belong here:** any particular site's hostnames, certificates or credentials. Those
are configuration, supplied per deployment.
