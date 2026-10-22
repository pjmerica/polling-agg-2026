"""Build model_audit/MODEL_AUDIT.md from MODEL_AUDIT_template.md, inserting the generated tables in
model_audit/tables/ ({{TABLE:<name>}} -> tables/<name>.md). No number in those tables is typed by hand.

    py "State election results/model_audit/build_audit.py"
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    tmpl = open(os.path.join(HERE, "MODEL_AUDIT_template.md"), encoding="utf-8").read()

    def table(m):
        path = os.path.join(HERE, "tables", m.group(1) + ".md")
        if not os.path.exists(path):
            return f"*(not generated yet: tables/{m.group(1)}.md)*"
        text = open(path, encoding="utf-8").read().strip()
        # demote the generated headings so the table's top level sits just under this document's
        # '###' sections (level 4), keeping their nesting
        levels = [len(h) for h in re.findall(r"(?m)^(#{1,6}) ", text)]
        shift = 4 - min(levels) if levels else 0
        return re.sub(r"(?m)^(#{1,6}) ", lambda h: "#" * min(6, len(h.group(1)) + shift) + " ", text)

    out = re.sub(r"\{\{TABLE:([a-z_]+)\}\}", table, tmpl)
    with open(os.path.join(HERE, "MODEL_AUDIT.md"), "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote model_audit/MODEL_AUDIT.md")


if __name__ == "__main__":
    main()
