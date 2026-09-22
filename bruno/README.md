# Bruno API collections

This folder holds [Bruno](https://www.usebruno.com/) collections for exercising the project's
APIs, in the [opencollection](https://opencollection.io/) format.

## Layout

```
bruno/
├── public/     Collections committed to the repo. Generic, no secrets.
├── private/    Your local working copies. Gitignored — never committed.
├── .env        Your local secrets (base URLs, tokens, credentials). Gitignored.
└── copy_collection.sh
```

- **`public/`** holds the source-of-truth collections. Per this repo's open-core rule, nothing in
  here may contain deployment-specific or secret values — see `AGENTS.md`.
- **`private/`** is where you actually run collections from in Bruno, so you can fill in
  environment values and `.env` secrets without risking a commit. Anything under `private/` is
  gitignored automatically.
- **`.env`** holds secrets shared across your private collections (e.g. credentials for a local
  server instance). Gitignored; copy `.env.example` if one exists, otherwise create it yourself.

## Using a collection

`/onboarding` already runs this for every collection under `public/`, using `bruno/.env.example`
to create `bruno/.env` if you don't have one yet — Bruno itself is optional, but the private
copies are there and ready the moment you install it. Come back here when you need to refresh a
collection after `public/` changes, or if you're setting this up by hand.

> **Windows:** `copy_collection.sh` is a Bash script, and Command Prompt can't run it — `./` and
> `.sh` files aren't things cmd.exe understands. Run it from **Git Bash**, or from
> cmd.exe/PowerShell with `bash copy_collection.sh <collection-name>`.

1. Copy the collection you want out of `public/` and into `private/`:

   ```sh
   ./copy_collection.sh <collection-name>
   ```

   For example, `./copy_collection.sh server_collection` copies `public/server_collection` to
   `private/server_collection_private`, and copies `bruno/.env` into it as
   `private/server_collection_private/.env`. The `_private` suffix is also written into the
   copy's `opencollection.yml`, so the Bruno desktop UI shows a name you can tell apart from the
   public collection.

   Re-running the script for the same collection overwrites the existing private copy, so any
   local edits you made to that collection are lost — re-apply them after copying, or edit the
   collection's environments only.

2. Open `bruno/private/<collection-name>_private` in the Bruno app and work from there.

3. If `public/` gets new requests or environments, re-run the script to pick them up (see the
   overwrite note above).

## `copy_collection.sh`

```sh
./copy_collection.sh <collection-name>
```

- Fails with a usage message if no collection name is given.
- Fails if `public/<collection-name>` doesn't exist.
- Deletes any existing `private/<collection-name>_private` and replaces it with a fresh copy of
  `public/<collection-name>`, renamed to `<collection-name>_private`.
- Rewrites the `name:` field in the copy's `opencollection.yml` to match, so Bruno's UI shows
  the `_private` suffix too.
- Copies `bruno/.env` into the private collection as `.env`, if it exists (warns and continues
  if it doesn't).
