"""CI script: validate coverage threshold from coverage.xml."""
import xml.etree.ElementTree as ET
import sys

THRESHOLD = 95

try:
    tree = ET.parse("coverage.xml")
    root = tree.getroot()
    rate = float(root.attrib.get("line-rate", "0"))
    pct = int(rate * 100)
    print(f"Coverage: {pct}%")
    if pct < THRESHOLD:
        print(f"Coverage below threshold of {THRESHOLD}%")
        sys.exit(1)
    else:
        print(f"Coverage passes threshold (>={THRESHOLD}%)")
except FileNotFoundError:
    print("coverage.xml not found, skipping coverage validation")
