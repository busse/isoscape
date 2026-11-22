"""How the redlining story shows a share: once, from the unrounded value in numbers.json.

measure.py writes every share unrounded, and the page, its charts and its figures all go through
`pct`, so a percentage is rounded exactly once (half up) wherever it appears. d3 rounded twice
(to three places in numbers.json, then again with Python's half-to-even rule), which turned
64.53% into 64 and 22.53% into 22; test/redlining-page.test.ts checks the page against this rule.
"""
import math


def pct(x):
    """`x` (a share, 0 to 1) as a whole percent, rounded half up, as a string."""
    return str(math.floor(x * 100 + 0.5))
