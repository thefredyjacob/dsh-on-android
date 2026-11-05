#!/usr/bin/env python3
"""Apply the Android/Termux compatibility patches to a global DSH install.

Idempotent. Each changed file gets a one-time `.bak` sibling.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

LOADER_SHIM = r"""'use strict';

// Android/Termux fallback for node-addon-require-builtin.
// DSH's Cordis loader uses this only to reach Node internals; it already
// catches failures and falls back to its documented no-internals path.
// Launch Node with --expose-internals so require() can resolve internal/*.
function requireBuiltin(id) {
  return require(id);
}

function isAllowedInternalId() {
  return false;
}

function getBindingInfo() {
  return {
    mode: 'javascript-fallback',
    product: 'dsh',
    backend: 'js',
    abi: 'js',
    bindingPath: null,
    bindingSource: 'js-fallback',
    localBindingPath: null,
    optionalPackageName: null,
    optionalBinaryRelativePath: null,
  };
}

module.exports = {
  requireBuiltin,
  isAllowedInternalId,
  getBindingInfo,
  default: { requireBuiltin, isAllowedInternalId, getBindingInfo },
};
"""

FS_LOCAL_FALLBACK = '''const linkFile = internals.linkFile ?? (process.platform === "android" ? async (from, to) => {
\t\ttry {
\t\t\tawait lstat(to);
\t\t} catch (error) {
\t\t\tif (error.code === "ENOENT") {
\t\t\t\tawait rename(from, to);
\t\t\t\treturn;
\t\t\t}
\t\t\tthrow error;
\t\t}
\t\tconst exists = new Error("EEXIST: file already exists");
\t\texists.code = "EEXIST";
\t\tthrow exists;
\t} : link);'''


def global_root() -> Path:
    override = os.environ.get("DSH_ROOT")
    if override:
        return Path(override)
    try:
        return Path(
            subprocess.check_output(
                ["npm", "root", "-g"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"cannot find npm global root: {error}") from error


ROOT = global_root()
DSH = ROOT / "@deepseek-ai" / "dsh"


def resolve(name: str) -> Path:
    for base in (DSH / "node_modules", ROOT):
        candidate = base / name
        if candidate.exists():
            return candidate
    raise SystemExit(f"package not found: {name}")


def backup(path: Path) -> None:
    backup_path = path.with_name(path.name + ".bak")
    if not backup_path.exists():
        shutil.copy2(path, backup_path)


def patch_loader() -> str:
    path = resolve("node-addon-require-builtin") / "lib" / "index.js"
    text = path.read_text()
    if "javascript-fallback" in text:
        return "loader: already patched"
    backup(path)
    path.write_text(LOADER_SHIM)
    return "loader: patched"


def patch_flock() -> str:
    path = resolve("@deepseek-ai/node-addon-system") / "lib" / "flock.js"
    text = path.read_text()
    if "Android/Termux has no prebuilt" in text:
        return "flock: already patched"
    marker = "export async function tryLockExclusive(fd) {"
    if marker not in text:
        raise SystemExit(f"flock marker not found in {path}")
    insert = (
        marker
        + "\n    // Android/Termux has no prebuilt POSIX flock addon. DSH runs one\n"
        + "    // host process here, so the advisory session-file lock is a no-op.\n"
        + '    if (process.platform === "android")\n        return;'
    )
    backup(path)
    path.write_text(text.replace(marker, insert, 1))
    return "flock: patched"


def patch_fs_local() -> str:
    path = resolve("@deepseek-ai/dsh-fs-local") / "lib" / "index.js"
    text = path.read_text()
    if 'internals.linkFile ?? (process.platform === "android"' in text:
        return "fs-local: already patched"
    old = "const linkFile = internals.linkFile ?? link;"
    if old not in text:
        raise SystemExit(f"fs-local marker not found in {path}")
    backup(path)
    path.write_text(text.replace(old, FS_LOCAL_FALLBACK, 1))
    return "fs-local: patched"


def patch_session() -> str:
    path = (
        resolve("@deepseek-ai/dsh-session-persistence-jsonl")
        / "lib"
        / "index.js"
    )
    text = path.read_text()
    if 'if (process.platform === "android") await rename(tmp, finalPath);' in text:
        return "session: already patched"

    old_import = (
        'import { link, lstat, mkdir, mkdtemp, open, readFile, readdir, '
        'realpath, rm, stat, truncate } from "node:fs/promises";'
    )
    new_import = (
        'import { link, lstat, mkdir, mkdtemp, open, readFile, readdir, '
        'realpath, rename, rm, stat, truncate } from "node:fs/promises";'
    )
    old_link = "\t\t\tawait link(tmp, finalPath);\n\t\t\tlinked = true;"
    new_link = (
        '\t\t\tif (process.platform === "android") await rename(tmp, finalPath);\n'
        "\t\t\telse await link(tmp, finalPath);\n"
        "\t\t\tlinked = true;"
    )

    if old_import not in text:
        raise SystemExit(f"session import marker not found in {path}")
    if old_link not in text:
        raise SystemExit(f"session link marker not found in {path}")

    backup(path)
    text = text.replace(old_import, new_import, 1)
    text = text.replace(old_link, new_link, 1)
    path.write_text(text)
    return "session: patched"


def main() -> None:
    if not DSH.exists():
        raise SystemExit(f"DSH not found at {DSH}; install it first")
    print(f"DSH root: {DSH}")
    for step in (patch_loader, patch_flock, patch_fs_local, patch_session):
        print(step())
    print("done. launch with scripts/dsh-android, not plain dsh.")


if __name__ == "__main__":
    main()
