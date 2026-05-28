"""
Patches get_steps() in core/i18n.py to include step 5.
Run once from the project root:  python patch_get_steps.py
"""
import os, ast, re

TARGET = os.path.join(os.path.dirname(__file__), "core", "i18n.py")

with open(TARGET, encoding="utf-8") as f:
    content = f.read()

# Replace get_steps function body to loop over steps 1-5
old_patterns = [
    # common variants that return 4 steps
    ('get_steps(locale: str = "en") -> list:\n    """Return list of (number_str, label) tuples for the stepper."""\n    return [\n        (str(i), get(f"step.{i}", locale))\n        for i in range(1, 5)\n    ]',
     'get_steps(locale: str = "en") -> list:\n    """Return list of (number_str, label) tuples for the stepper."""\n    return [\n        (str(i), get(f"step.{i}", locale))\n        for i in range(1, 6)\n    ]'),
]

patched = False
for old, new in old_patterns:
    if old in content:
        content = content.replace(old, new)
        patched = True
        break

# Fallback: regex replacement on range(1, N)
if not patched:
    new_content, n = re.subn(
        r'(def get_steps.*?range\(1,\s*)(\d+)(\))',
        lambda m: m.group(1) + '6' + m.group(3),
        content, flags=re.DOTALL)
    if n:
        content = new_content
        patched = True

if not patched:
    print("WARNING: Could not auto-patch get_steps(). "
          "Manually change range(1, 5) to range(1, 6) in get_steps().")
else:
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)
    try:
        ast.parse(content)
        print("SUCCESS: get_steps() now returns 5 steps.")
    except SyntaxError as e:
        print(f"ERROR at line {e.lineno}: {e.msg}")