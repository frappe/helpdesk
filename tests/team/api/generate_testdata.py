"""Generate API test data from the OpenAPI spec.

For every input of every operation (query/path parameters and request-body
properties, nested objects included) this produces:

  * equivalence partitions (EP): each valid class once, and each invalid
    class once. An enum gives one valid class per member plus the invalid
    class "not a member"; a string gives "typical", plus "missing" when the
    input is required and "wrong type".
  * 3-point boundary values (BVA): just below, at and just above every limit
    found in the schema (minLength, maxLength, minimum, maximum).

Each case changes exactly one input, so an invalid case carries one invalid
value. The API tests are parametrised from the JSON this script writes; they
contain no hand-picked input values.

Usage: python generate_testdata.py [--spec openapi.yaml] [--out generated/testdata.json]
"""

import argparse
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
MISSING = "__MISSING__"  # sentinel: leave the input out of the request


def three_point(limit):
    """3-point boundary values around a limit: below, at, above."""
    return [limit - 1, limit, limit + 1]


def resolve(spec, schema):
    while "$ref" in schema:
        node = spec
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        schema = node
    return schema


def walk_inputs(spec, schema, prefix, required):
    """Yield (dotted path, leaf schema, is_required) for every leaf input."""
    schema = resolve(spec, schema)
    if schema.get("type") == "object":
        needed = set(schema.get("required", []))
        for name, child in schema.get("properties", {}).items():
            yield from walk_inputs(spec, child, [*prefix, name], required and name in needed)
    else:
        yield ".".join(prefix), schema, required


def operation_inputs(spec, operation):
    for parameter in operation.get("parameters", []):
        schema = resolve(spec, parameter["schema"])
        # a path parameter cannot be left out: the URL would name another endpoint
        required = parameter.get("required", False) and parameter["in"] != "path"
        yield f"{parameter['in']}:{parameter['name']}", schema, required
    body = operation.get("requestBody")
    if body:
        schema = body["content"]["application/json"]["schema"]
        for path, leaf, required in walk_inputs(spec, schema, [], body.get("required", False)):
            yield f"body:{path}", leaf, required


def string_of_length(length):
    return ("Ticket " + "x" * length)[:length] if length >= 7 else "x" * length


def cases_for_input(schema, required):
    """Return a list of (technique, class name, value, is_valid)."""
    if schema.get("x-fixed"):
        return []  # constant that selects the operation itself, not a test input
    cases = []
    kind = schema.get("type", "string")
    fixture = schema.get("x-fixture")

    if "enum" in schema:
        for member in schema["enum"]:
            cases.append(("EP", f"valid member '{member}'", member, True))
        cases.append(("EP", "not a member of the enum", "Not-A-Listed-Value", False))
    elif kind == "string":
        if fixture:
            cases.append(("EP", "existing value", {"fixture": fixture}, True))
            cases.append(("EP", "unknown value", schema.get("x-invalid-example", "unknown"), False))
        else:
            typical = schema.get("example") or string_of_length(20)
            cases.append(("EP", "typical valid string", typical, True))
        if not fixture and "enum" not in schema:
            cases.append(("EP", "wrong type (number)", 12345, False))
        low, high = schema.get("minLength"), schema.get("maxLength")
        if not fixture:
            if low is not None:
                for length in three_point(low):
                    cases.append(("BVA", f"length {length} (minLength {low})", string_of_length(length), length >= low))
            if high is not None:
                for length in three_point(high):
                    cases.append(("BVA", f"length {length} (maxLength {high})", string_of_length(length), length <= high))
    elif kind in ("integer", "number"):
        low, high = schema.get("minimum"), schema.get("maximum")
        middle = schema.get("example", low if low is not None else 1)
        cases.append(("EP", "typical valid number", middle, True))
        cases.append(("EP", "wrong type (text)", "not-a-number", False))
        if low is not None:
            for value in three_point(low):
                cases.append(("BVA", f"value {value} (minimum {low})", value, value >= low))
        if high is not None:
            for value in three_point(high):
                cases.append(("BVA", f"value {value} (maximum {high})", value, value <= high))

    if required:
        cases.append(("EP", "missing required input", MISSING, False))
    return cases


def generate(spec):
    operations = []
    cases = []
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            op_id = operation["operationId"]
            operations.append(
                {
                    "operationId": op_id,
                    "method": method.upper(),
                    "path": path,
                    "role": operation.get("x-test-role", "customer"),
                    "responses": sorted(operation["responses"]),
                }
            )
            for input_path, schema, required in operation_inputs(spec, operation):
                for number, (technique, name, value, valid) in enumerate(cases_for_input(schema, required), 1):
                    cases.append(
                        {
                            "id": f"{op_id}/{input_path.split(':', 1)[1]}/{technique}{number:02d}",
                            "operationId": op_id,
                            "input": input_path,
                            "technique": technique,
                            "class": name,
                            "value": value,
                            "valid": valid,
                            "expect_status": 200
                            if valid
                            else schema.get("x-reject-status", operation.get("x-reject-status", 417)),
                        }
                    )
    return {"spec_version": spec["info"]["version"], "operations": operations, "cases": cases}


def summarise(data):
    lines = [f"spec version {data['spec_version']}: {len(data['cases'])} cases"]
    per_input = {}
    for case in data["cases"]:
        key = (case["operationId"], case["input"])
        counts = per_input.setdefault(key, {"EP": 0, "BVA": 0, "valid": 0, "invalid": 0})
        counts[case["technique"]] += 1
        counts["valid" if case["valid"] else "invalid"] += 1
    for (operation, input_path), counts in per_input.items():
        lines.append(
            f"  {operation:<14}{input_path:<26} EP {counts['EP']:>2}  BVA {counts['BVA']:>2}"
            f"  valid {counts['valid']:>2}  invalid {counts['invalid']:>2}"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", default=str(HERE / "openapi.yaml"))
    parser.add_argument("--out", default=str(HERE / "generated" / "testdata.json"))
    args = parser.parse_args()
    spec = yaml.safe_load(Path(args.spec).read_text())
    data = generate(spec)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n")
    print(summarise(data))
    print(f"written: {out}")


if __name__ == "__main__":
    main()
