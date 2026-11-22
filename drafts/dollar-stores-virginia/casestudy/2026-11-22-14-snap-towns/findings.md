# Step 14: findings. Which towns get Dollar Generals (November 22, 11:00)

The tests are as stated in `hypotheses.md` (10:50, before any number). The script is
`tools/stories/dollar-stores/snap_towns.py`, and the outputs are `towns_tests.csv`,
`towns_thirds.csv` and `towns.csv.gz`. Run time about 1 minute, first try.

## Results (six held-out states, 1,460 small incorporated places)

| Test | Places | Stores | Stores per household, for 10 more points of SNAP share | 95% interval | Verdict |
|---|---|---|---|---|---|
| T1 Dollar General, the place itself | 1,460 | 1,615 | 1.13x | 1.10-1.17 | holds |
| T2 Dollar General, within 5 km of the center | 1,461 | 1,615 | 1.25x | 1.19-1.31 | holds |
| T3 grocery (contrast) | 1,460 | 1,603 | 1.17x | 1.12-1.22 | holds |
| T3 convenience (contrast) | 1,460 | 4,087 | 1.21x | 1.16-1.25 | holds |
| Virginia, 186 places (exploratory) | 186 | 155 | 1.12x | 1.01-1.24 | no verdict |

Poisson regression with log households and state; bootstrap over places, 2,000 resamples.

| Towns by share of households on SNAP | Places | SNAP share | Dollar Generals per 1,000 households | Groceries per 1,000 households | Towns with at least one Dollar General |
|---|---|---|---|---|---|
| Lowest third | 487 | 0 to 13.6% | 0.74 | 0.78 | 61% |
| Middle third | 486 | 13.6 to 24.3% | 1.05 | 0.99 | 77% |
| Highest third | 487 | 24.4 to 83.3% | 1.20 | 1.21 | 77% |

## Reading

- Towns where more households get SNAP have more Dollar Generals per household. T1 holds and
  T2 agrees.
- They also have more grocery stores and convenience stores per household, by as much or more.
  So the link is not special to Dollar General. Higher-SNAP towns simply have more food stores
  for their size, of every kind we counted.
  - A likely reason, not tested: such towns tend to be poorer, more rural market towns that
    serve people from the countryside around them.
- Exploratory, not pre-stated: the ratio of Dollar Generals to groceries is flat across the
  thirds (0.96, 1.07, 0.99).
- **Against the stated bar,** T1 and T2 pass, but the contrasts show the link is not specific
  to Dollar General. A poster sentence would have to say that. Something like: "Towns where
  more families use SNAP have more stores of every kind for their size, Dollar Generals
  included." That is true but does not answer "why the edge?", so it is not proposed for the
  poster.

## Together with step 13

- **Within a town,** SNAP households do not predict where the store sits.
- **Across towns,** SNAP households predict more stores of all kinds, not more Dollar Generals
  in particular.
- **So** SNAP is not the answer to "why the edge?". The answer stays roads and timing.

## Not done

- No independent review, because no poster text depends on it yet.
