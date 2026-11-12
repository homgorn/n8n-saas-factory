# Runtime on H: (large installs live off C:)

C: ran out of space (1.1 GB free) during npm installs — that is what made the n8n and template
installs fail or hang, not a broken toolchain. Everything heavy now lives on H:, with junctions
left in place so the repository paths keep working unchanged.

## Layout

| Path on H: | Junction from | What |
| --- | --- | --- |
| `H:\saas-runtime\projects\analyzer\node_modules` | `saas-factory/analyzer/node_modules` | analyzer deps (68 MB) |
| `H:\saas-runtime\n8n` | `%TEMP%\n8n-local` | local n8n install (856 MB, 1932 packages) |
| `H:\saas-runtime\data\n8n-docs-source` | `n8n-docs-source` | cloned n8n docs (52 MB) |
| `H:\saas-runtime\data\n8n-instance` | — | n8n user folder (SQLite, logs) |
| `H:\saas-runtime\npm-cache` | — | npm cache (`npm config set cache`) |
| `H:\saas-runtime\ms-playwright` | — | Playwright browsers |

Effect: C: went from 1.1 GB free to 8.2 GB free; H: holds ~21 GB free.

## Two constraints that cost time — read before moving anything again

**1. A directory literally named `node_modules` breaks nested resolution.**
The first layout put the package *contents* in `H:\saas-runtime\node_modules\<project>\`.
Node and TypeScript skip any ancestor directory named `node_modules` while walking up, so a
package resolving a sibling dependency failed to find it: `@playwright/test` could not resolve
`playwright/test`, and `@supabase/ssr` could not resolve `@supabase/supabase-js`, which surfaced
as unrelated-looking type errors (`no exported member 'test'`, implicit `any`).
The shape must be `<project>/node_modules/<package>` — one level deeper than it looks.

**2. Next.js cannot run with `node_modules` behind a junction.**
Next's bundler computes a relative path to its own `dist/client/app-next-dev.js` from the project
root. Through a junction the real path lives on another drive and the computation breaks:

```
Module not found: Can't resolve './H:/saas-runtime/projects/ai-tool/node_modules/next/dist/client/app-next-dev.js'
```

So `saas-factory/templates/ai-tool/node_modules` lives on **C: as a real directory** (468 MB).
Everything that does not need a bundler (analyzer, n8n, caches) stays on H: behind junctions.
Measure before assuming: `C:` has room for it, and the earlier exhaustion was caused by a
1.9 GB n8n install, not by the template.

## Running the local n8n

```bash
cd H:\saas-runtime\n8n
set N8N_USER_FOLDER=H:\saas-runtime\data\n8n-instance
set N8N_PORT=5678
set N8N_HOST=127.0.0.1
set WEBHOOK_URL=http://127.0.0.1:5678/
set N8N_ENCRYPTION_KEY=n8n-saas-factory-local-dev-key-32chars
.\node_modules\.bin\n8n.cmd start
```

Health: `curl http://127.0.0.1:5678/healthz`

## Importing the F008 sync workflow

```bash
cd H:\saas-runtime\n8n
.\node_modules\.bin\n8n.cmd import:workflow --input=C:\susa\ai\N8N\n8n-wiki\workflows\f008-sync-workflow.json
```

## Rule of thumb

Any install that will exceed ~500 MB goes to `H:\saas-runtime\`. Keep the repository itself on C:
(it is small) and junction only the heavy directories.
