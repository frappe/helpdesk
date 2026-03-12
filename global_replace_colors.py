import os
import re

directory = "desk/src"

replacements = {
    r"\bbg-white\b": "bg-surface-white",
    r"\bbg-gray-50\b": "bg-surface-gray-2",
    r"\bbg-gray-100\b": "bg-surface-gray-3",
    r"\bbg-gray-200\b": "bg-surface-gray-4",
    r"\bbg-gray-300\b": "bg-surface-gray-5",
    r"\bbg-gray-400\b": "bg-surface-gray-6",
    r"\bbg-gray-500\b": "bg-surface-gray-7",
    r"\bbg-gray-600\b": "bg-surface-gray-8",
    r"\bbg-gray-700\b": "bg-surface-gray-9",
    r"\bbg-gray-800\b": "bg-surface-black",
    r"\bbg-gray-900\b": "bg-surface-black",
    r"\btext-gray-50\b": "text-ink-gray-1",
    r"\btext-gray-100\b": "text-ink-gray-1",
    r"\btext-gray-200\b": "text-ink-gray-2",
    r"\btext-gray-300\b": "text-ink-gray-3",
    r"\btext-gray-400\b": "text-ink-gray-4",
    r"\btext-gray-500\b": "text-ink-gray-5",
    r"\btext-gray-600\b": "text-ink-gray-6",
    r"\btext-gray-700\b": "text-ink-gray-7",
    r"\btext-gray-800\b": "text-ink-gray-8",
    r"\btext-gray-900\b": "text-ink-gray-9",
    r"\bborder-gray-50\b": "border-outline-gray-1",
    r"\bborder-gray-100\b": "border-outline-gray-1",
    r"\bborder-gray-200\b": "border-outline-gray-2",
    r"\bborder-gray-300\b": "border-outline-gray-3",
    r"\bborder-gray-400\b": "border-outline-gray-4",
    r"\bborder-gray-500\b": "border-outline-gray-5",
    r"\bborder-gray-600\b": "border-outline-gray-6",
    r"\bborder-gray-700\b": "border-outline-gray-7",
    r"\bborder-gray-800\b": "border-outline-gray-8",
    r"\bborder-gray-900\b": "border-outline-gray-9",
    r"\bhover:bg-gray-50\b": "hover:bg-surface-gray-2",
    r"\bhover:bg-gray-100\b": "hover:bg-surface-gray-3",
    r"\bhover:bg-gray-200\b": "hover:bg-surface-gray-4",
    r"\bhover:bg-gray-300\b": "hover:bg-surface-gray-5",
    r"\bhover:bg-gray-400\b": "hover:bg-surface-gray-6",
    r"\bhover:bg-gray-500\b": "hover:bg-surface-gray-7",
    r"\bhover:bg-gray-600\b": "hover:bg-surface-gray-8",
    r"\bhover:text-gray-500\b": "hover:text-ink-gray-5",
    r"\bhover:text-gray-600\b": "hover:text-ink-gray-6",
    r"\bhover:text-gray-700\b": "hover:text-ink-gray-7",
    r"\bhover:text-gray-800\b": "hover:text-ink-gray-8",
    r"\bhover:text-gray-900\b": "hover:text-ink-gray-9",
    r"\bfill-gray-500\b": "fill-ink-gray-5",
    r"\bfill-gray-600\b": "fill-ink-gray-6",
    r"\bfill-gray-700\b": "fill-ink-gray-7",
    r"\bfill-gray-800\b": "fill-ink-gray-8",
    r"\bfill-gray-900\b": "fill-ink-gray-9",
    r"\bplaceholder-gray-400\b": "placeholder-ink-gray-4",
    r"\bplaceholder-gray-500\b": "placeholder-ink-gray-5",
    r"\bplaceholder-gray-600\b": "placeholder-ink-gray-6",
    r"\bplaceholder-gray-700\b": "placeholder-ink-gray-7",
    r"\bplaceholder-gray-800\b": "placeholder-ink-gray-8",
    r"\bplaceholder-gray-900\b": "placeholder-ink-gray-9",
    r"\bdivide-gray-100\b": "divide-outline-gray-1",
    r"\bdivide-gray-200\b": "divide-outline-gray-2",
    r"\bdivide-gray-300\b": "divide-outline-gray-3",
    r"\bdivide-gray-400\b": "divide-outline-gray-4",
    r"\bdivide-gray-500\b": "divide-outline-gray-5",
}


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath}")


for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".vue") or file.endswith(".ts") or file.endswith(".js"):
            filepath = os.path.join(root, file)
            process_file(filepath)
