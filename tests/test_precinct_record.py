"""Precinct record: nothing voter-level or personal goes in, and links are only the state's own general-election results."""
import csv
import importlib.util
import io
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("precinct_record", os.path.join(ROOT, "Precinct data 2026", "precinct_record.py"))
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)


def test_nc_counts_keep_no_names_or_addresses():
    head = ["voter_reg_num", "voter_last_name", "voter_first_name", "voter_street_address", "voter_mail_addr1"] + pr.NC_KEYS
    row = ["12345", "Doe", "Jane", "1 Main St", "PO Box 9", "WAKE", "01-01", "CD 2", "DEM", "MAIL", "MAIL", "10/20/2026", "ACCEPTED"]
    raw = io.StringIO()
    w = csv.writer(raw)
    w.writerow(head)
    w.writerow(row)
    w.writerow(row)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("absentee.csv", raw.getvalue())
    out = pr.nc_counts(buf.getvalue()).decode()
    for private in ("Doe", "Jane", "Main St", "PO Box", "12345"):
        assert private not in out
    rows = list(csv.DictReader(io.StringIO(out)))
    assert len(rows) == 1 and rows[0]["ballots"] == "2" and rows[0]["ballot_rtn_dt"] == "10/20/2026"


def test_change_log_loses_the_officials_name():
    src = "Timestamp,Username,Precinct,NewValue\r\n11/03/2026 19:31:55,Some Official,502 - RUE,152\r\n".encode("utf-8-sig")
    out = pr.drop_column(src, "Username").decode()
    assert "Some Official" not in out and "Username" not in out
    assert "11/03/2026 19:31:55,502 - RUE,152" in out


def test_drop_column_leaves_other_files_whole():
    src = b"a,b\n1,2\n"
    assert pr.drop_column(src, "Username") == b"a,b\n1,2\n"


def test_links_only_general_precinct_files_on_the_states_own_site():
    html = """
    <a href="/f/2026-General-Precinct-Results.xlsx">2026 General</a>
    <a href="/f/2026-Primary-Precinct-Results.xlsx">2026 Primary</a>
    <a href="/f/2024-General-Precinct-Results.xlsx">2024 General</a>
    <a href="/f/2026-General-Summary.xlsx">2026 General summary</a>
    <a href="/f/2026-General-Precinct-Voter-History.csv">who voted</a>
    <a href="/f/2026-General-Absentee-Voters-by-Precinct.csv">absentee</a>
    <a href="https://example.com/2026-General-Precinct-Results.xlsx">elsewhere</a>
    <a href="/f/{*CODE*}_2026_General_Precinct.xlsx">placeholder</a>
    <a href="/page/2026-general-precinct-results">a page, not a file</a>
    """
    found = pr.links_on_page(html, "https://sos.state.example.gov/results/")
    assert list(found) == ["https://sos.state.example.gov/f/2026-General-Precinct-Results.xlsx"]


def test_stable_ignores_publish_stamps_but_not_votes():
    a = b'{"asOf":"2026-11-05T01:00:00Z","publishVersionId":"x","blobName":"a_1.csv","voteCount":5}'
    b = b'{"asOf":"2026-11-05T02:00:00Z","publishVersionId":"y","blobName":"a_2.csv","voteCount":5}'
    c = b'{"asOf":"2026-11-05T02:00:00Z","publishVersionId":"y","blobName":"a_2.csv","voteCount":6}'
    assert pr.stable(a) == pr.stable(b)
    assert pr.stable(a) != pr.stable(c)
