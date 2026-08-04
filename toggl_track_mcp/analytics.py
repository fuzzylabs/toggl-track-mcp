"""Helpers for Toggl's Analytics API (custom reports).

Custom reports are the multi-chart dashboards behind
``track.toggl.com/reports/{organization_id}/custom/{dashboard_id}``. They are
served by Toggl's ``analytics`` API, which is **not** part of the published
Reports API v3 documentation and has no OpenAPI spec. Everything here was
derived from the Toggl web app's own API client and verified against the live
API. It authenticates with the ordinary API token, but treat it as unversioned:
Toggl can change it without notice.

Quirks of that API shape the code below:

* Durations come back in **milliseconds**, unlike Reports v3 which uses seconds.
* The query engine rejects some field combinations a saved chart may contain:
  ``attributes`` alongside ``groupings``, and ``ordinations`` on a property that
  is not grouped (a ``client_name`` sort on a ``client_id`` grouping, for
  instance). Both return a 500 rather than a validation error, so
  :func:`build_query` strips them and the ordering is applied locally instead.
* A saved chart may carry the page size the UI renders it with, and a paginated
  response carries no total count. :func:`build_query` drops it so the whole
  result set comes back rather than a page that looks complete.
* Queries are quota'd separately from the rest of the API: responses carry
  ``x-toggl-quota-remaining`` and ``x-toggl-quota-resets-in``, measured at 240
  queries per hour. Worth keeping in mind before running a report in a loop.

This module holds only pure functions and models. The HTTP calls live on
``TogglAPIClient`` in ``toggl_client.py``.
"""

import calendar
from datetime import date, timedelta
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict

ANALYTICS_BASE_URL = "https://api.track.toggl.com/analytics/api"

#: Earliest date the Toggl web app uses for its "all time" preset.
ALL_TIME_START = date(2006, 1, 1)

#: Maps an id column in a result row to the dictionary that names it.
_DICTIONARY_FOR_COLUMN = {
    "client_id": "clients",
    "group_id": "user_groups",
    "project_id": "projects",
    "tag_id": "tags",
    "task_id": "tasks",
    "user_group_id": "user_groups",
    "user_id": "users",
    "workspace_id": "workspaces",
}


class TogglAnalyticsChart(BaseModel):
    """A single chart within a custom report."""

    id: Optional[int] = None
    organization_id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[str] = None
    pinned: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None
    query: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    creator_name: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class TogglAnalyticsDashboard(BaseModel):
    """A custom report ("dashboard") and the charts it contains."""

    id: Optional[int] = None
    organization_id: Optional[int] = None
    name: Optional[str] = None
    pinned: Optional[bool] = None
    locked: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    grid_items: Optional[List[Dict[str, Any]]] = None
    charts: Optional[List[TogglAnalyticsChart]] = None
    chart_summary: Optional[Dict[str, Any]] = None
    link: Optional[Dict[str, Any]] = None
    permissions: Optional[List[Dict[str, Any]]] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


def _add_months(day: date, months: int) -> date:
    """Shift a date by whole months, clamping to the end of the target month."""
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def _start_of_month(day: date) -> date:
    return day.replace(day=1)


def _end_of_month(day: date) -> date:
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


def _start_of_week(day: date, beginning_of_week: int) -> date:
    """Start of the week containing ``day``.

    ``beginning_of_week`` follows Toggl's convention: 0 is Sunday, 1 is Monday.
    """
    offset = (day.weekday() - (beginning_of_week - 1)) % 7
    return day - timedelta(days=offset)


def _start_of_quarter(day: date) -> date:
    return date(day.year, 3 * ((day.month - 1) // 3) + 1, 1)


def _start_of_semester(day: date) -> date:
    """First day of the current half-year (January or July)."""
    return date(day.year, 1 if day.month <= 6 else 7, 1)


def resolve_period(
    preset: Optional[str],
    today: Optional[date] = None,
    beginning_of_week: int = 1,
    custom_from: Optional[str] = None,
    custom_to: Optional[str] = None,
) -> Tuple[str, str]:
    """Resolve a Toggl date preset into an inclusive ``(from, to)`` date pair.

    The ranges mirror the web app's own preset definitions so a report run
    through this client covers the same days it does in the UI.

    Args:
        preset: Preset name, e.g. ``prevMonth``. ``custom`` uses the explicit
            dates. ``None`` is treated as ``thisMonth``, matching the app's
            behaviour for a report saved without a period.
        today: Reference date (defaults to the current date).
        beginning_of_week: 0 for Sunday, 1 for Monday.
        custom_from: Start date for the ``custom`` preset (YYYY-MM-DD).
        custom_to: End date for the ``custom`` preset (YYYY-MM-DD).

    Raises:
        ValueError: If the preset is unknown, or ``custom`` is missing dates.
    """
    day = today or date.today()
    week_start = _start_of_week(day, beginning_of_week)
    semester_start = _start_of_semester(day)
    quarter_start = _start_of_quarter(day)

    if preset in (None, ""):
        preset = "thisMonth"

    if preset == "custom":
        if not custom_from or not custom_to:
            raise ValueError(
                "Report uses a custom date range but has no dates saved. "
                "Pass start_date and end_date."
            )
        return custom_from, custom_to

    ranges: Dict[str, Tuple[date, date]] = {
        "today": (day, day),
        "yesterday": (day - timedelta(days=1), day - timedelta(days=1)),
        "thisWeek": (week_start, week_start + timedelta(days=6)),
        "prevWeek": (week_start - timedelta(days=7), week_start - timedelta(days=1)),
        "weekToDate": (week_start, day),
        "last2Weeks": (week_start - timedelta(days=14), week_start - timedelta(days=1)),
        "thisMonth": (_start_of_month(day), _end_of_month(day)),
        "prevMonth": (
            _start_of_month(_add_months(_start_of_month(day), -1)),
            _end_of_month(_add_months(_start_of_month(day), -1)),
        ),
        "monthToDate": (_start_of_month(day), day),
        "thisQuarter": (
            quarter_start,
            _end_of_month(_add_months(quarter_start, 2)),
        ),
        "quarterToDate": (quarter_start, day),
        "lastQuarter": (
            _add_months(quarter_start, -3),
            quarter_start - timedelta(days=1),
        ),
        "thisSemester": (
            semester_start,
            _end_of_month(_add_months(semester_start, 5)),
        ),
        "semesterToDate": (semester_start, day),
        "lastSemester": (
            _add_months(semester_start, -6),
            semester_start - timedelta(days=1),
        ),
        "last30Days": (day - timedelta(days=29), day),
        "last90Days": (day - timedelta(days=89), day),
        "last12Months": (
            _start_of_month(_add_months(day, -11)),
            _end_of_month(day),
        ),
        "thisYear": (date(day.year, 1, 1), date(day.year, 12, 31)),
        "yearToDate": (date(day.year, 1, 1), day),
        "prevYear": (date(day.year - 1, 1, 1), date(day.year - 1, 12, 31)),
        "allTime": (ALL_TIME_START, date(day.year + 2, 12, 31)),
    }

    if preset not in ranges:
        raise ValueError(
            f"Unknown date preset '{preset}'. Pass start_date and end_date instead."
        )

    start, end = ranges[preset]
    return start.isoformat(), end.isoformat()


def period_for_dashboard(
    dashboard: TogglAnalyticsDashboard,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    today: Optional[date] = None,
    fallback_beginning_of_week: Optional[int] = None,
) -> Dict[str, str]:
    """Work out the date window to run a report over.

    A complete pair of explicit dates wins; otherwise the report's saved preset
    is resolved.

    Args:
        dashboard: The report, whose preferences hold the preset and week start
        start_date: Explicit start date, supplied together with ``end_date``
        end_date: Explicit end date, supplied together with ``start_date``
        today: Reference date for relative presets (defaults to the current date)
        fallback_beginning_of_week: Week start to use when the report does not
            save one. The report's own setting always takes precedence, so that
            a week-based preset covers the same days it does in the UI whoever
            runs it.
    """
    if (start_date is None) != (end_date is None):
        raise ValueError("start_date and end_date must be provided together")

    if start_date is not None and end_date is not None:
        try:
            parsed_start = date.fromisoformat(start_date)
            parsed_end = date.fromisoformat(end_date)
        except ValueError as error:
            raise ValueError(
                "start_date and end_date must use YYYY-MM-DD format"
            ) from error
        if parsed_start > parsed_end:
            raise ValueError("start_date must be on or before end_date")
        return {"from": start_date, "to": end_date}

    preferences = dashboard.preferences or {}
    date_period = preferences.get("datePeriod") or {}

    # Toggl's own field name carries this typo.
    saved_beginning_of_week = preferences.get("begginingOfWeek")
    if saved_beginning_of_week is not None:
        beginning_of_week = saved_beginning_of_week
    elif fallback_beginning_of_week is not None:
        beginning_of_week = fallback_beginning_of_week
    else:
        beginning_of_week = 1

    resolved_from, resolved_to = resolve_period(
        date_period.get("preset"),
        today=today,
        beginning_of_week=beginning_of_week,
        custom_from=date_period.get("from") or start_date,
        custom_to=date_period.get("to") or end_date,
    )
    return {"from": start_date or resolved_from, "to": end_date or resolved_to}


def _grouped_properties(query: Dict[str, Any]) -> List[str]:
    return [
        grouping.get("property")
        for grouping in query.get("groupings") or []
        if grouping.get("property")
    ]


def build_query(
    dashboard: TogglAnalyticsDashboard,
    chart: TogglAnalyticsChart,
    period: Dict[str, str],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Build an analytics query payload for one chart of a custom report.

    Merges the chart's saved query with the report-level filters and the
    resolved period, and removes the field combinations the query engine
    rejects.

    Returns:
        The payload, and the ordinations that were removed so the caller can
        apply them to the returned rows instead.
    """
    query: Dict[str, Any] = dict(chart.query or {})
    query["period"] = period

    filters: List[Dict[str, Any]] = list(query.get("filters") or [])
    filters.extend(dashboard.filters or [])
    if filters:
        query["filters"] = filters

    groupings = _grouped_properties(query)

    # An `attributes` list is only valid on an ungrouped (detail) query.
    if groupings:
        query.pop("attributes", None)

    # If any sort references an ungrouped property, apply the complete sequence
    # locally. Splitting it between the API and a stable local sort would make a
    # locally-applied secondary key override the remote primary key.
    local_ordinations: List[Dict[str, Any]] = []
    if query.get("ordinations"):
        saved_ordinations = query["ordinations"]
        if any(
            ordination.get("property") not in groupings
            for ordination in saved_ordinations
        ):
            local_ordinations = saved_ordinations
            query.pop("ordinations", None)

    # A saved chart can carry the page size the UI renders it with. Sending it
    # would return one page and give the caller no way to tell that more rows
    # exist, since the response carries no total count. Omitting pagination
    # returns the whole result set: measured against a 7-month ungrouped query,
    # 7,582 rows came back, matching count(time_entry_id) for the same window.
    query.pop("pagination", None)

    query.pop("v3_query_params", None)

    return query, local_ordinations


def _dictionary_name(
    dictionaries: Dict[str, Any], dictionary: str, entity_id: Any
) -> Optional[str]:
    entries = dictionaries.get(dictionary) or {}
    entry = entries.get(str(entity_id))
    if isinstance(entry, dict):
        name = entry.get("name")
        return str(name) if name is not None else None
    if entry is not None:
        return str(entry)
    return None


def resolve_rows(
    rows: List[Dict[str, Any]],
    dictionaries: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Turn raw result rows into readable ones.

    Adds a ``*_name`` for every id column the response has a dictionary for,
    and converts millisecond durations to seconds.
    """
    dictionaries = dictionaries or {}
    resolved: List[Dict[str, Any]] = []

    for row in rows:
        item = dict(row)
        for column, value in row.items():
            dictionary = _DICTIONARY_FOR_COLUMN.get(column)
            if dictionary and value is not None:
                name = _dictionary_name(dictionaries, dictionary, value)
                if name is not None:
                    item[column.replace("_id", "_name")] = name
            if column.endswith("duration") and isinstance(value, (int, float)):
                item[f"{column}_seconds"] = int(value) // 1000
        resolved.append(item)

    return resolved


def _sort_value(column: str, row: Dict[str, Any]) -> Tuple[int, float, str]:
    """Sort key that orders numbers numerically and everything else as text.

    A dropped ordination is often on an aggregate column (`sum_duration`), so
    comparing those as strings would put 900 before 1000. The leading rank keys
    the two kinds apart, since a tuple of mixed types cannot be compared.
    """
    value = row.get(column)
    if value is None:
        # Nulls are repositioned after the sort; this only has to be stable.
        return (2, 0.0, "")
    if isinstance(value, (int, float)):  # bool included, and ordered 0 before 1
        return (0, float(value), "")
    return (1, 0.0, str(value).lower())


def sort_rows(
    rows: List[Dict[str, Any]], ordinations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Apply ordinations the query engine could not, ignoring unknown columns."""
    ordered = list(rows)

    for ordination in reversed(ordinations):
        prop = ordination.get("property")
        if not prop or not any(prop in row for row in ordered):
            continue
        column = str(prop)
        descending = str(ordination.get("direction", "ASC")).upper() == "DESC"
        nulls_last = str(ordination.get("nulls", "first")).lower() == "last"

        ordered.sort(key=partial(_sort_value, column), reverse=descending)

        # Null placement is independent of direction, so position it after the
        # sort rather than letting `reverse` flip it.
        missing = [row for row in ordered if row.get(column) is None]
        if missing:
            present = [row for row in ordered if row.get(column) is not None]
            ordered = present + missing if nulls_last else missing + present

    return ordered


def summarise_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Total the numeric aggregate columns across rows."""
    totals: Dict[str, Any] = {}
    for row in rows:
        for column, value in row.items():
            if (column.startswith("sum_") or column == "count") and isinstance(
                value, (int, float)
            ):
                totals[column] = totals.get(column, 0) + value
    if "sum_duration" in totals:
        totals["sum_duration_seconds"] = int(totals["sum_duration"]) // 1000
    return totals
