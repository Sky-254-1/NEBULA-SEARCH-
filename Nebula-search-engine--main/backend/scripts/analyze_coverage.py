"""Analyze coverage.xml and print top gaps."""
import xml.etree.ElementTree as ET
from collections import defaultdict

tree = ET.parse("coverage.xml")
root = tree.getroot()
by_file: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))

for cls in root.findall(".//class"):
    fn = cls.get("filename", "")
    for line in cls.findall("lines/line"):
        total_hits = by_file[fn]
        missed = 1 if int(line.get("hits", 0)) == 0 else 0
        by_file[fn] = (total_hits[0] + 1, total_hits[1] + missed)

rows = []
for fn, (total, missed) in by_file.items():
    if missed > 0:
        rows.append((missed, total, (total - missed) / total * 100, fn))
rows.sort(reverse=True)

rate = float(root.get("line-rate", 0)) * 100
print(f"Overall line-rate: {rate:.1f}%")
print(f"Total missed: {sum(r[0] for r in rows)}")
print("\nTop 50 by missed lines:")
for missed, total, pct, fn in rows[:50]:
    print(f"  {missed:4d}/{total:4d} ({pct:5.1f}%)  {fn}")
