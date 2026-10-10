"""Fail when a staged Studio JSON changed but kept its `modified` timestamp.

Studio's migrate sync skips a file whose `modified` is unchanged, so the edit
would never reach any site.
"""

import json
import subprocess
import sys


def staged_json(ref_path):
    result = subprocess.run(["git", "show", ref_path], capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else None


def main(paths):
    stale = []
    for path in paths:
        old, new = staged_json(f"HEAD:{path}"), staged_json(f":{path}")
        if not isinstance(old, dict) or not isinstance(new, dict) or "modified" not in new:
            continue
        if old != new and old.get("modified") == new["modified"]:
            stale.append(path)

    for path in stale:
        print(f"{path}: content changed but `modified` did not; bump it or migrate skips the file")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
