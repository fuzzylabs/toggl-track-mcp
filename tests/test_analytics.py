"""Tests for the Analytics API helpers (custom reports)."""

from datetime import date

import pytest

from toggl_track_mcp.analytics import (
    TogglAnalyticsChart,
    TogglAnalyticsDashboard,
    build_query,
    period_for_dashboard,
    resolve_period,
    resolve_rows,
    sort_rows,
    summarise_rows,
)

# A Monday, so week boundaries are unambiguous in the assertions below.
TODAY = date(2026, 8, 3)


class TestResolvePeriod:
    """Preset date ranges must match the ones the Toggl UI uses."""

    @pytest.mark.parametrize(
        "preset,expected",
        [
            ("today", ("2026-08-03", "2026-08-03")),
            ("yesterday", ("2026-08-02", "2026-08-02")),
            ("thisWeek", ("2026-08-03", "2026-08-09")),
            ("prevWeek", ("2026-07-27", "2026-08-02")),
            ("weekToDate", ("2026-08-03", "2026-08-03")),
            ("last2Weeks", ("2026-07-20", "2026-08-02")),
            ("thisMonth", ("2026-08-01", "2026-08-31")),
            ("prevMonth", ("2026-07-01", "2026-07-31")),
            ("monthToDate", ("2026-08-01", "2026-08-03")),
            ("thisQuarter", ("2026-07-01", "2026-09-30")),
            ("quarterToDate", ("2026-07-01", "2026-08-03")),
            ("lastQuarter", ("2026-04-01", "2026-06-30")),
            ("thisSemester", ("2026-07-01", "2026-12-31")),
            ("semesterToDate", ("2026-07-01", "2026-08-03")),
            ("lastSemester", ("2026-01-01", "2026-06-30")),
            ("last30Days", ("2026-07-05", "2026-08-03")),
            ("last90Days", ("2026-05-06", "2026-08-03")),
            ("last12Months", ("2025-09-01", "2026-08-31")),
            ("thisYear", ("2026-01-01", "2026-12-31")),
            ("yearToDate", ("2026-01-01", "2026-08-03")),
            ("prevYear", ("2025-01-01", "2025-12-31")),
            ("allTime", ("2006-01-01", "2028-12-31")),
        ],
    )
    def test_presets(self, preset, expected):
        assert resolve_period(preset, today=TODAY) == expected

    def test_missing_preset_defaults_to_this_month(self):
        assert resolve_period(None, today=TODAY) == ("2026-08-01", "2026-08-31")
        assert resolve_period("", today=TODAY) == ("2026-08-01", "2026-08-31")

    def test_week_starting_sunday(self):
        assert resolve_period("thisWeek", today=TODAY, beginning_of_week=0) == (
            "2026-08-02",
            "2026-08-08",
        )

    def test_custom_uses_supplied_dates(self):
        assert resolve_period(
            "custom",
            today=TODAY,
            custom_from="2026-01-15",
            custom_to="2026-02-15",
        ) == ("2026-01-15", "2026-02-15")

    def test_custom_without_dates_raises(self):
        with pytest.raises(ValueError, match="custom date range"):
            resolve_period("custom", today=TODAY)

    def test_unknown_preset_raises(self):
        with pytest.raises(ValueError, match="Unknown date preset"):
            resolve_period("sinceTheDawnOfTime", today=TODAY)

    def test_month_end_clamping(self):
        """A 31st does not roll into the next month when shifting back."""
        assert resolve_period("prevMonth", today=date(2026, 3, 31)) == (
            "2026-02-01",
            "2026-02-28",
        )

    def test_defaults_to_current_date(self):
        start, end = resolve_period("today")
        assert start == end == date.today().isoformat()


class TestPeriodForDashboard:
    def test_explicit_dates_win(self):
        dashboard = TogglAnalyticsDashboard(
            id=1, preferences={"datePeriod": {"preset": "prevMonth"}}
        )
        assert period_for_dashboard(
            dashboard, start_date="2026-01-01", end_date="2026-01-31"
        ) == {"from": "2026-01-01", "to": "2026-01-31"}

    def test_saved_preset_is_resolved(self):
        dashboard = TogglAnalyticsDashboard(
            id=1, preferences={"datePeriod": {"preset": "prevMonth"}}
        )
        assert period_for_dashboard(dashboard, today=TODAY) == {
            "from": "2026-07-01",
            "to": "2026-07-31",
        }

    def test_saved_week_start_is_honoured(self):
        dashboard = TogglAnalyticsDashboard(
            id=1,
            preferences={"datePeriod": {"preset": "thisWeek"}, "begginingOfWeek": 0},
        )
        assert period_for_dashboard(dashboard, today=TODAY) == {
            "from": "2026-08-02",
            "to": "2026-08-08",
        }

    def test_saved_custom_range(self):
        dashboard = TogglAnalyticsDashboard(
            id=1,
            preferences={
                "datePeriod": {
                    "preset": "custom",
                    "from": "2026-05-01",
                    "to": "2026-05-31",
                }
            },
        )
        assert period_for_dashboard(dashboard, today=TODAY) == {
            "from": "2026-05-01",
            "to": "2026-05-31",
        }

    def test_no_preferences_falls_back_to_this_month(self):
        assert period_for_dashboard(TogglAnalyticsDashboard(id=1), today=TODAY) == {
            "from": "2026-08-01",
            "to": "2026-08-31",
        }


class TestBuildQuery:
    def _chart(self, **query):
        return TogglAnalyticsChart(id=9, type="table", query=query)

    def test_merges_report_filters_and_period(self):
        dashboard = TogglAnalyticsDashboard(
            id=1,
            filters=[
                {
                    "operator": "and",
                    "value": None,
                    "conditions": [
                        {"property": "user_id", "operator": "in", "value": [7]}
                    ],
                }
            ],
        )
        chart = self._chart(
            groupings=[{"property": "client_id"}],
            aggregations=[{"function": "sum", "property": "duration"}],
            filters=[{"property": "workspace_id", "operator": "=", "value": 456}],
        )

        query, dropped = build_query(
            dashboard, chart, {"from": "2026-07-01", "to": "2026-07-31"}
        )

        assert query["period"] == {"from": "2026-07-01", "to": "2026-07-31"}
        assert query["filters"] == [
            {"property": "workspace_id", "operator": "=", "value": 456},
            dashboard.filters[0],
        ]
        assert dropped == []

    def test_attributes_dropped_when_grouped(self):
        """The query engine 500s on attributes alongside groupings."""
        chart = self._chart(
            groupings=[{"property": "client_id"}],
            attributes=[{"property": "duration"}],
        )

        query, _ = build_query(TogglAnalyticsDashboard(id=1), chart, {"from": "a"})

        assert "attributes" not in query

    def test_attributes_kept_without_grouping(self):
        chart = self._chart(attributes=[{"property": "duration"}])

        query, _ = build_query(TogglAnalyticsDashboard(id=1), chart, {"from": "a"})

        assert query["attributes"] == [{"property": "duration"}]

    def test_ordination_on_ungrouped_property_is_returned_for_local_sorting(self):
        chart = self._chart(
            groupings=[{"property": "client_id"}],
            ordinations=[
                {"property": "client_name", "direction": "ASC"},
                {"property": "client_id", "direction": "DESC"},
            ],
        )

        query, dropped = build_query(
            TogglAnalyticsDashboard(id=1), chart, {"from": "a"}
        )

        assert query["ordinations"] == [{"property": "client_id", "direction": "DESC"}]
        assert dropped == [{"property": "client_name", "direction": "ASC"}]

    def test_all_ordinations_dropped_removes_the_key(self):
        chart = self._chart(
            groupings=[{"property": "client_id"}],
            ordinations=[{"property": "client_name", "direction": "ASC"}],
        )

        query, dropped = build_query(
            TogglAnalyticsDashboard(id=1), chart, {"from": "a"}
        )

        assert "ordinations" not in query
        assert len(dropped) == 1

    def test_v3_query_params_removed(self):
        chart = self._chart(v3_query_params=None, groupings=[])

        query, _ = build_query(TogglAnalyticsDashboard(id=1), chart, {"from": "a"})

        assert "v3_query_params" not in query

    def test_chart_query_is_not_mutated(self):
        chart = self._chart(groupings=[{"property": "client_id"}])
        original = dict(chart.query)

        build_query(TogglAnalyticsDashboard(id=1), chart, {"from": "a"})

        assert chart.query == original

    def test_empty_chart_query(self):
        query, dropped = build_query(
            TogglAnalyticsDashboard(id=1), TogglAnalyticsChart(id=9), {"from": "a"}
        )

        assert query == {"period": {"from": "a"}}
        assert dropped == []


class TestResolveRows:
    def test_ids_resolved_and_durations_converted(self):
        rows = [{"client_id": 101, "user_id": 202, "sum_duration": 22200000}]
        dictionaries = {
            "clients": {"101": {"id": 101, "name": "Acme Corp"}},
            "users": {"202": {"id": 202, "name": "Alex"}},
        }

        resolved = resolve_rows(rows, dictionaries)

        assert resolved[0]["client_name"] == "Acme Corp"
        assert resolved[0]["user_name"] == "Alex"
        assert resolved[0]["sum_duration_seconds"] == 22200
        assert resolved[0]["sum_duration"] == 22200000

    def test_missing_dictionary_entry_is_left_alone(self):
        resolved = resolve_rows([{"client_id": 1, "sum_duration": 1000}], {})

        assert "client_name" not in resolved[0]
        assert resolved[0]["sum_duration_seconds"] == 1

    def test_null_id_is_not_resolved(self):
        resolved = resolve_rows([{"client_id": None}], {"clients": {}})

        assert "client_name" not in resolved[0]

    def test_plain_string_dictionary_values(self):
        resolved = resolve_rows([{"user_id": 3}], {"users": {"3": "Alex"}})

        assert resolved[0]["user_name"] == "Alex"

    def test_no_dictionaries_argument(self):
        assert resolve_rows([{"count": 2}]) == [{"count": 2}]


class TestSortRows:
    def test_sorts_by_resolved_name(self):
        rows = [{"client_name": "Zeta"}, {"client_name": "Alpha"}]

        ordered = sort_rows(rows, [{"property": "client_name", "direction": "ASC"}])

        assert [row["client_name"] for row in ordered] == ["Alpha", "Zeta"]

    def test_descending(self):
        rows = [{"client_name": "Alpha"}, {"client_name": "Zeta"}]

        ordered = sort_rows(rows, [{"property": "client_name", "direction": "DESC"}])

        assert [row["client_name"] for row in ordered] == ["Zeta", "Alpha"]

    def test_nulls_first_by_default(self):
        rows = [{"client_name": "Alpha"}, {"other": 1}]

        ordered = sort_rows(rows, [{"property": "client_name", "nulls": "first"}])

        assert ordered[0] == {"other": 1}

    def test_nulls_last(self):
        rows = [{"other": 1}, {"client_name": "Alpha"}]

        ordered = sort_rows(rows, [{"property": "client_name", "nulls": "last"}])

        assert ordered[-1] == {"other": 1}

    def test_unknown_column_is_ignored(self):
        rows = [{"client_name": "Zeta"}, {"client_name": "Alpha"}]

        ordered = sort_rows(rows, [{"property": "nope", "direction": "ASC"}])

        assert ordered == rows

    def test_ordination_without_property_is_ignored(self):
        rows = [{"client_name": "Zeta"}]

        assert sort_rows(rows, [{"direction": "ASC"}]) == rows

    def test_no_ordinations_returns_rows_unchanged(self):
        rows = [{"client_name": "Zeta"}]

        assert sort_rows(rows, []) == rows


class TestSummariseRows:
    def test_totals_numeric_aggregates(self):
        rows = [
            {"sum_duration": 1000, "count": 2, "client_name": "A"},
            {"sum_duration": 2500, "count": 3, "client_name": "B"},
        ]

        totals = summarise_rows(rows)

        assert totals["sum_duration"] == 3500
        assert totals["count"] == 5
        assert totals["sum_duration_seconds"] == 3

    def test_no_duration_column(self):
        assert summarise_rows([{"count": 1}]) == {"count": 1}

    def test_empty_rows(self):
        assert summarise_rows([]) == {}
