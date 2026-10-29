# Original Halo service reference

`halo_server.py` is an unchanged snapshot of the original loopback-only service
source. It is retained as deployment reference rather than advertised as a
portable server command. Do not run it directly from this directory.

Its original layout expects the following sibling directories under a chosen
parent (typically `~/ai`):

```text
qwen-shared-memory/
  shared_memory.py
  server.py             # copy of halo_server.py
  private/auth.json     # locally generated; never commit
qwen-context-store-v4/
  encoder.py
  model/onnx/model.onnx
  model/tokenizer.json
```

With dependencies from the `dense` extra installed, place the server at that
layout's `qwen-shared-memory/server.py`, create a private `auth.json` containing
a `token` field with a newly generated strong credential, and restrict the
private directory to its owner. The auth file must have mode 0600 on Linux.
Set `QWEN_SHARED_DB` explicitly to your own database path, then run `server.py`.
It listens only on `127.0.0.1:8748` and indexes in a background CPU thread.

All routes require `Authorization: Bearer <your-local-token>`:

| Route | Purpose |
|---|---|
| GET `/status` | Bounded counts and metadata events |
| POST `/search` | Arguments accepted by `Memory.search` |
| POST `/publish` | Arguments accepted by `Memory.publish` |

The reference server does not expose HTTP capture; the original integrations
capture through trusted local Python code. Use the Python API for ingestion
in this release. Its token grants administrative access, not per-user scopes.
Keep it on loopback or behind an authenticated, encrypted host connection.

The service reference is not part of the portable unit-test coverage. No
installer alters system services or any existing agent installation.
