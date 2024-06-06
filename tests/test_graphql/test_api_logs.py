from datetime import datetime
from systemd import journal


def assert_log_entry_equals_to_journal_entry(api_entry, journal_entry):
    assert api_entry["message"] == journal_entry["MESSAGE"]
    assert (
        datetime.fromisoformat(api_entry["timestamp"])
        == journal_entry["__REALTIME_TIMESTAMP"]
    )
    assert api_entry["priority"] == journal_entry["PRIORITY"]
    assert api_entry.get("systemdUnit") == journal_entry.get("_SYSTEMD_UNIT")
    assert api_entry.get("systemdSlice") == journal_entry.get("_SYSTEMD_SLICE")


def take_from_journal(j, limit, next):
    entries = []
    for _ in range(0, limit):
        entry = next(j)
        if entry["MESSAGE"] != "":
            entries.append(entry)
    return entries


API_GET_LOGS_WITH_UP_BORDER = """
query TestQuery($upCursor: String) {
    logs {
        paginated(limit: 4, upCursor: $upCursor) {
            pageMeta {
                upCursor
                downCursor
            }
            entries {
                message
                timestamp
                priority
                systemdUnit
                systemdSlice
            }
        }
    }
}
"""

API_GET_LOGS_WITH_DOWN_BORDER = """
query TestQuery($downCursor: String) {
    logs {
        paginated(limit: 4, downCursor: $downCursor) {
            pageMeta {
                upCursor
                downCursor
            }
            entries {
                message
                timestamp
                priority
                systemdUnit
                systemdSlice
            }
        }
    }
}
"""


def test_graphql_get_logs_with_up_border(authorized_client):
    j = journal.Reader()
    j.seek_tail()

    # < - cursor
    # <- - log entry will be returned by API call.
    # ...
    # log <
    # log <-
    # log <-
    # log <-
    # log <-
    # log

    expected_entries = take_from_journal(j, 6, lambda j: j.get_previous())
    expected_entries.reverse()

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_LOGS_WITH_UP_BORDER,
            "variables": {"upCursor": expected_entries[0]["__CURSOR"]},
        },
    )
    assert response.status_code == 200

    expected_entries = expected_entries[1:-1]
    returned_entries = response.json()["data"]["logs"]["paginated"]["entries"]

    assert len(returned_entries) == len(expected_entries)

    for api_entry, journal_entry in zip(returned_entries, expected_entries):
        assert_log_entry_equals_to_journal_entry(api_entry, journal_entry)


def test_graphql_get_logs_with_down_border(authorized_client):
    j = journal.Reader()
    j.seek_head()
    j.get_next()

    # < - cursor
    # <- - log entry will be returned by API call.
    # log
    # log <-
    # log <-
    # log <-
    # log <-
    # log <
    # ...

    expected_entries = take_from_journal(j, 5, lambda j: j.get_next())

    response = authorized_client.post(
        "/graphql",
        json={
            "query": API_GET_LOGS_WITH_DOWN_BORDER,
            "variables": {"downCursor": expected_entries[-1]["__CURSOR"]},
        },
    )
    assert response.status_code == 200

    expected_entries = expected_entries[:-1]
    returned_entries = response.json()["data"]["logs"]["paginated"]["entries"]

    assert len(returned_entries) == len(expected_entries)

    for api_entry, journal_entry in zip(returned_entries, expected_entries):
        assert_log_entry_equals_to_journal_entry(api_entry, journal_entry)
