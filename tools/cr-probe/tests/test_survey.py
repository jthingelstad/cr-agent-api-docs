"""Surveys turn a hunch into a verdict backed by every week the API remembers."""

from crprobe.survey import SENTINEL_FINISH_TIME, finish_time


class FakeClient:
    def __init__(self, items):
        self._items = items

    def get(self, path):
        class R:
            ok = True
            status = 200
            body = {"items": self._items}
        return R()


def week(season, section, *, colosseum, rank1_finish):
    stakes = 100 if colosseum else 20
    others = [
        {"rank": n, "trophyChange": -stakes,
         "clan": {"name": f"c{n}", "finishTime": SENTINEL_FINISH_TIME}}
        for n in (2, 3, 4, 5)
    ]
    return {
        "seasonId": season, "sectionIndex": section, "createdDate": "20260907T093404.000Z",
        "standings": [{"rank": 1, "trophyChange": stakes,
                       "clan": {"name": "us", "finishTime": rank1_finish}}] + others,
    }


def test_claim_holds_when_colosseum_is_all_sentinel_and_normal_weeks_are_not():
    client = FakeClient([
        week(135, 4, colosseum=True, rank1_finish=SENTINEL_FINISH_TIME),
        week(135, 3, colosseum=False, rank1_finish="20260830T093404.000Z"),
        week(134, 3, colosseum=True, rank1_finish=SENTINEL_FINISH_TIME),
    ])

    result = finish_time(client, "#TAG")

    assert result["holds"] is True
    assert result["colosseum_weeks"] == 2 and result["normal_weeks"] == 1


def test_a_single_counterexample_breaks_the_claim():
    """This is the guard against publishing a rule seen once and assumed general."""
    client = FakeClient([
        week(135, 4, colosseum=True, rank1_finish="20260907T093404.000Z"),
        week(135, 3, colosseum=False, rank1_finish="20260830T093404.000Z"),
    ])

    assert finish_time(client, "#TAG")["holds"] is False


def test_no_colosseum_week_in_range_means_unproven_not_proven():
    client = FakeClient([week(135, 3, colosseum=False, rank1_finish="20260830T093404.000Z")])

    result = finish_time(client, "#TAG")

    assert result["holds"] is False, "absence of evidence must not read as confirmation"


def test_rows_carry_the_evidence_the_docs_table_needs():
    client = FakeClient([week(135, 4, colosseum=True, rank1_finish=SENTINEL_FINISH_TIME)])

    (row,) = finish_time(client, "#TAG")["rows"]

    assert row["colosseum"] and row["all_sentinel"] and row["rank1_is_sentinel"]
    assert row["season"] == 135 and row["section"] == 4
