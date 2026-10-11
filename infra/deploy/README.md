# `infra/deploy/` — deployment to on-premise hosts

The stack every deployed machine runs: testing, staging and every user installation alike. They
differ only in their environment file.

| File | What it is |
|---|---|
| `compose.yaml` | The four services: `web` (Caddy plus the built frontend), `server`, `db` (Postgres) and `garage-s3-storage` (S3 file storage). Images are pulled, never built here |
| `Caddyfile` | Baked into the web image. Serves the frontend, forwards `/api` to the server, and obtains HTTPS certificates for `DOMAIN` |
| `garage.toml` | Garage's configuration, mounted into its container. Single node, sqlite metadata, no replication |

Only ports 80 and 443 are published. Postgres and Garage are reachable from the other containers
and nowhere else.

**Never run `docker compose down -v`** on a deployed machine. It deletes the database, the stored
files and Caddy's certificates; re-requesting certificates repeatedly can hit Let's Encrypt's rate
limits.

## How images are published

Images are built once and then promoted: moving a site to a new environment moves a pointer to
an image that already exists, and never rebuilds it. There are three pointers, one per
environment: `:testing`, `:staging` and `:production`.

### Building: `.github/workflows/deploy.yml`

Runs on every push to `main` or to a `release/*` branch. It builds and starts this stack exactly as
below, checks that Caddy serves the site and `/api/health_check`, and only then pushes
`ghcr.io/<owner>/armada-server` and `armada-web`:

| Pushed to | Images tagged with | Pointer moved |
|---|---|---|
| `main` | the commit they were built from | `:testing` |
| `release/X.Y.Z` (a hot fix) | the next release candidate, `X.Y.Z-rc.N` | `:staging` |

A commit whose images already exist in the registry is not built again. A manual run from the
Actions tab can be a dry run that pushes nothing.

### Promoting: `.github/workflows/release.yml`

Run by hand, once the team decides a build is ready to move on. It never builds anything: it
gives images that already exist a new name and moves a pointer to them. It has two steps:

1. **Testing to staging.** The build on `:testing` becomes a release candidate: the images are
   tagged `X.Y.Z-rc.N`, `:staging` is moved to them, and a `vX.Y.Z-rc.N` git tag and a GitHub
   pre-release are created on the commit they were built from.
2. **Staging to production.** The candidate on `:staging` gets its plain version: the same images
   are tagged `X.Y.Z` and moved to `:production`, a `vX.Y.Z` git tag is added to the same commit,
   the `release/X.Y.Z` branch is created from it, and the GitHub release is published with the
   image digests and this directory's `compose.yaml` and `garage.toml`, as they were in that
   commit. It is marked as the latest release.

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
  production; the newest **Pre-release** is the candidate most recently sent to staging.
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
