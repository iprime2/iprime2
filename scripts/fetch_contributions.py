#!/usr/bin/env python3
"""Fetch the public contribution calendar (no token) into data/contributions.json."""
import json
import os
import re
import urllib.request
from html.parser import HTMLParser

USER = os.environ.get("GH_USER", "iprime2")
URL = f"https://github.com/users/{USER}/contributions"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}  # id -> {"date", "level"}
        self.counts = {}  # id -> count
        self._tip_for = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (a.get("class") or "") and a.get("data-date"):
            self.cells[a["id"]] = {"date": a["data-date"], "level": int(a.get("data-level") or 0)}
        elif tag == "tool-tip":
            self._tip_for = a.get("for")

    def handle_data(self, data):
        if self._tip_for:
            m = re.match(r"\s*([\d,]+) contribution", data)
            self.counts[self._tip_for] = int(m.group(1).replace(",", "")) if m else 0

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self._tip_for = None


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-readme-heatmap"})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8")
    cal = Calendar()
    cal.feed(html)
    days = sorted(
        ({"date": c["date"], "level": c["level"], "count": cal.counts.get(i, 0)} for i, c in cal.cells.items()),
        key=lambda d: d["date"],
    )
    if len(days) < 300:
        raise SystemExit(f"calendar looks wrong: {len(days)} days")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"user": USER, "days": days}, f, indent=0)
    print(f"{len(days)} days, {sum(d['count'] for d in days)} contributions")


if __name__ == "__main__":
    main()
