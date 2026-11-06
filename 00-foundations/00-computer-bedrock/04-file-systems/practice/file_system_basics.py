"""File system basics: metadata vs content, atomic writes, hard links, and durability.

Works in a temp directory and cleans up after itself.

Run:
    python file_system_basics.py
"""

import os
import stat
import tempfile
import time
from pathlib import Path


def atomic_write(path: Path, text: str) -> None:
    """Write to a temp file, flush to disk, then rename over the target.
    Readers see the old file or the new file, never a half-written one."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())                      # ask the OS to push bytes to the device
    os.replace(tmp, path)                         # atomic rename on the same filesystem


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        f = root / "notes.txt"
        f.write_text("hello")
        st = f.stat()
        print("1. metadata lives beside the content:")
        print(f"   size={st.st_size} bytes, modified={time.ctime(st.st_mtime)}, is_file={stat.S_ISREG(st.st_mode)}")

        print("\n2. atomic write:")
        atomic_write(f, "version 2")
        print(f"   contents now {f.read_text()!r}; leftover .tmp files: {list(root.glob('*.tmp'))}")

        print("\n3. hard links: two names, one file:")
        link = root / "alias.txt"
        try:
            os.link(f, link)
            link.write_text("changed via alias")
            print(f"   notes.txt now reads {f.read_text()!r}; link count = {f.stat().st_nlink}")
        except OSError as e:
            print("   hard links not supported here:", e)

        print("\n4. directories are just files that map names to entries:")
        (root / "sub").mkdir()
        (root / "sub" / "a.txt").write_text("a")
        print("   listing:", sorted(p.name for p in root.rglob("*")))

        print("\nWhy it matters: never overwrite a file in place if a crash mid-write would corrupt it.")
        print("Write-temp-then-rename is how editors, databases, and config writers stay safe.")
