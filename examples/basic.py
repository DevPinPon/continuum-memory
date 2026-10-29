"""A synthetic cross-session example; temporary database is removed on exit."""
import tempfile
from pathlib import Path
from shared_memory import Memory

with tempfile.TemporaryDirectory() as directory:
    memory = Memory(Path(directory) / "memory.sqlite3")
    memory.capture("example-agent", "old-session", "/work/demo", [
        {"id": "turn-1", "role": "user", "text": "The Vega caption color is amber."}
    ])
    result = memory.search("Vega caption color", project="/work/demo",
                           client="example-agent", session="new-session")
    assert result["selected"]
    assert "amber" in result["records"][0]["text"]
    print(result["records"][0]["text"])
