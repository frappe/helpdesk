"""Cosmic Ray filter: keep only mutants inside the business-rule scope.

Cosmic Ray generates mutants for every line of every module in `module-path`.
hd_ticket.py is ~1,500 lines but only four of its functions are in scope, so
this filter marks every pending mutant outside those functions as SKIPPED.
The scope definition is shared with scoped_coverage.py, so coverage and
mutation always measure the same code.

Usage: python mutation_scope_filter.py <session.sqlite> [--root <dir>]
"""

import ast
import sys
from pathlib import Path

from cosmic_ray.tools.filters.filter_app import FilterApp
from cosmic_ray.work_item import WorkerOutcome, WorkResult

sys.path.insert(0, str(Path(__file__).parent))
from scoped_coverage import SCOPE  # noqa: E402


def function_ranges(source_path, qualified_names):
    """Map 'Class.method' / 'function' names to inclusive (first, last) lines."""
    tree = ast.parse(Path(source_path).read_text())
    found = {}

    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                # the body only: decorators and the signature are not rule logic
                found[f"{prefix}{child.name}"] = (child.body[0].lineno, child.end_lineno)

    visit(tree, "")
    missing = [name for name in qualified_names if name not in found]
    if missing:
        raise SystemExit(f"scope functions not found in {source_path}: {missing}")
    return [found[name] for name in qualified_names]


class ScopeFilter(FilterApp):
    def description(self):
        return __doc__

    def add_args(self, parser):
        parser.add_argument("--root", default=".", help="Directory module paths are relative to")

    def filter(self, work_db, args):
        ranges_by_suffix = {
            suffix: function_ranges(Path(args.root) / suffix, names)
            for suffix, names in SCOPE.items()
            if names is not None
        }
        kept = skipped = 0
        for item in work_db.pending_work_items:
            mutation = item.mutations[0]
            path = str(mutation.module_path).replace("\\", "/")
            ranges = next((r for suffix, r in ranges_by_suffix.items() if path.endswith(suffix)), None)
            line = mutation.start_pos[0]
            if ranges is None or any(first <= line <= last for first, last in ranges):
                kept += 1
                continue
            work_db.set_result(
                item.job_id,
                WorkResult(output="Outside business-rule scope", worker_outcome=WorkerOutcome.SKIPPED),
            )
            skipped += 1
        print(f"scope filter: kept {kept} mutants, skipped {skipped} outside the scope")


if __name__ == "__main__":
    sys.exit(ScopeFilter().main())
