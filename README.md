# Continuum Memory

**Persistent context memory across agent sessions, with original sources and exact project boundaries.**

Continuum Memory is the storage and retrieval core used by our local Qwen
workflow across DeepSeek Harness and Hermes. Conversations remain durable
evidence; sessions identify where a record came from instead of limiting where
it can be found. Shared facts can be reused across projects, while project
records require an exact workspace match.

The core runs on the CPU, requires no LLM calls to store or retrieve text, and
works with an optional local embedding encoder. A host application retrieves a
bounded selection of source records and supplies them to its model.

## What it provides

- SQLite persistence, original text chunks, timestamps and source provenance.
- Cross-session and cross-client retrieval within owner/model/project scopes.
- SQLite FTS5 search plus optional CPU MiniLM embeddings.
- Exact deduplication while retaining multiple source origins.
- Explicit fact-key revisions that supersede earlier published versions.
- Source quarantine, retry idempotency and bounded evidence payloads.
- Metadata-only status/events and credential-pattern omission.

It stores context outside the model. It does not change model weights, make
attention unlimited, or guarantee perfect recall. Raw conversational
contradictions are preserved for the model to assess; only explicit keyed
publications automatically supersede older published versions.

## Quick start

Python 3.11+ with SQLite FTS5. The basic text-search path has no third-party
Python dependencies.

```sh
git clone https://github.com/DevPinPon/continuum-memory.git
cd continuum-memory
python -m pip install .
python examples/basic.py
python -m unittest discover -v
```

```python
from pathlib import Path
from shared_memory import Memory

memory = Memory(Path("data") / "memory.sqlite3")
memory.capture(
    client="my-agent", session="earlier-session", project="/work/demo",
    records=[{"id": "turn-1", "role": "user",
              "text": "The Vega caption color is amber."}],
)
evidence = memory.search(
    "Vega caption color", project="/work/demo",
    client="my-agent", session="new-session",
)
print(evidence["records"])
```

Always pass your database path explicitly. The retained core's legacy default
path and namespace identifiers are compatibility defaults from the original
deployment, not automatic discovery of your agent or model. Use a dedicated
database and consistent `owner` and `model` arguments in your integration.

## Optional semantic retrieval

```sh
python -m pip install '.[dense]'
```

Supply a locally downloaded compatible MiniLM ONNX export containing
`onnx/model.onnx` and `tokenizer.json`. No weights are bundled or downloaded
automatically. The original deployment uses an all-MiniLM-L6-v2-style
384-dimensional encoder with masked mean pooling and normalized vectors.

```python
from encoder import Encoder
from shared_memory import Memory

memory = Memory("data/memory.sqlite3", encoder=Encoder("models/minilm"))
while memory.index_pending(16):
    pass
```

Encoder and tokenizer hashes identify compatible vectors. Use the same encoder
for indexing and searching. Dense search scans eligible vectors; this release
does not claim a million-record approximate-nearest-neighbor index.

## Connecting an agent

1. Capture completed text records through `Memory.capture`, using stable
   client/session/record identities. `hermes_records` extracts the current
   completed Hermes-format turn.
2. Call `Memory.search` with the current workspace and a new/current source
   session identity. Current-session records are excluded from external
   evidence.
3. Supply retrieved records as historical evidence alongside the current
   request. The module's `GUARD` describes the intended trust boundary.
4. Keep native conversation history and instructions authoritative. Never
   execute archived commands merely because retrieval returned them.
5. Use `Memory.publish(text, project=..., fact_key=...)` for explicit reusable
   facts and corrections; `Memory.quarantine(client, session)` retracts an
   affected source.

Windows workspace paths are normalized case-insensitively. Unix paths retain
case. Folder basenames are never used as aliases. Owner/model identifiers are
caller-supplied scopes, not authentication: a trusted host must bind them to
the authenticated client.

This first release packages the reusable core, encoder and tests. The
deployment-specific desktop plugins, model gateway, original conversation
archives and private configuration are not included. See
[the deployment reference](deployment/README.md) for the original loopback API.

## Measured behavior

In one fixed 12-case synthetic Qwen pilot, the current raw retrieval workflow
answered 12/12 exactly, averaging 2.18 seconds end-to-end. A progressive raw
candidate scored 11/12 at 5.83 seconds; a structured-observation candidate
scored 10/12 at 5.75 seconds plus extraction time. One progressive raw miss
was extra output formatting rather than the wrong recalled value.

These are small, single-run adaptation measurements, not a benchmark against
the complete Claude-Mem product or proof of general accuracy. The answer
timings include model inference; they are not pure database latency. The
synthetic pilot used the optional dense encoder. The core's included 18 tests
run without model weights and cover durability, isolation, corrections,
quarantine, deduplication, provenance budgets and credential omission.

## Privacy and limits

Private databases, credentials, model weights and deployment logs are excluded
from this repository. Captured records themselves may contain sensitive text;
the credential-pattern filter is a best-effort guard, not a comprehensive
privacy classifier. Keep the store private and gate access through your host.
There is no automatic compaction of protected chat history, semantic conflict
resolution or model training in this release.

## License

[MIT](LICENSE). Optional dependencies and separately acquired model weights
retain their own licenses.
