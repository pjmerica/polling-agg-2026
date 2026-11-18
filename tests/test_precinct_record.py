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


def test_alaska_links_come_from_the_results_page_and_only_its_2026_folders():
    page = "https://www.elections.alaska.gov/election-results/"
    html = '''<a href="https://www.elections.alaska.gov/enr/26GENR/results/GA_ENR_Precinct_State_of_Alaska.csv">csv</a>
      <a href='/enr/26GENR/results/HD1.pdf'>HD01</a> <a href="/results/26GENR/RCV-Governor.pdf#top">rounds</a>
      <a href="/results/24GENR/ENRbyPrecinct.csv">2024</a> <a href="/election-results/e/?id=26prim">primary</a>
      <a href="https://example.com/enr/26GENR/results/x.csv">elsewhere</a>
      <a href="http://www.elections.alaska.gov/enr/26GENR/results/plain.csv">not https</a>'''
    import json
    src = json.load(open(os.path.join(ROOT, "Precinct data 2026", "sources.json"), encoding="utf-8"))["AK"][0]
    assert src["kind"] == "linked" and src["pages"] == [page]
    assert pr.links_matching(html, page, src["match"]) == [
        "https://www.elections.alaska.gov/enr/26GENR/results/GA_ENR_Precinct_State_of_Alaska.csv",
        "https://www.elections.alaska.gov/enr/26GENR/results/HD1.pdf",
        "https://www.elections.alaska.gov/results/26GENR/RCV-Governor.pdf",
    ]


def test_a_prove_you_are_human_page_is_not_saved_as_data(monkeypatch):
    challenge = b'<!DOCTYPE html><html lang="en"><head><title>Human Verification</title><script>window.awsWafCookieDomainList = [];</script>'
    assert pr.is_challenge(challenge)
    assert not pr.is_challenge(b"Precinct_name,Reporting_flag\n01-446 Aurora,captcha county\n")
    pages = {"https://s.gov/r/": b'<a href="/enr/26GENR/results/a.csv">a</a><a href="/enr/26GENR/results/b.html">b</a>',
             "https://s.gov/enr/26GENR/results/a.csv": b"x,y\n1,2\n", "https://s.gov/enr/26GENR/results/b.html": challenge}
    monkeypatch.setattr(pr, "get", lambda url: pages[url])
    st, src, rows, status = pr.fetch(("AK", {"kind": "linked", "pages": ["https://s.gov/r/"], "match": r"/enr/26GENR/.+\.(csv|html)$"}))
    assert [r[0] for r in rows] == ["a.csv"] and "b.html refused challenge" in status


def test_certificate_fallback_only_after_a_certificate_error_and_only_once(monkeypatch):
    import ssl
    import urllib.error
    calls, built = [], []

    class Resp:
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, n): return b"ok"

    def fake_urlopen(req, timeout=0, context=None):
        calls.append(context)
        if context is None:
            raise urllib.error.URLError(ssl.SSLCertVerificationError(1, "unable to get local issuer certificate"))
        return Resp()
    monkeypatch.setattr(pr.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(pr, "context_with_issuer", lambda host: built.append(host) or "CTX")
    monkeypatch.setattr(pr.time, "sleep", lambda s: None)
    monkeypatch.setattr(pr, "CONTEXTS", {})
    assert pr.get("https://state.example/a.csv") == b"ok" and pr.get("https://state.example/b.csv") == b"ok"
    assert built == ["state.example"] and calls == [None, "CTX", "CTX"]


# Throwaway test certificates (keys discarded): a self-signed root, and a leaf it signed whose
# "CA Issuers" link points at that root - what someone in the network path could serve.
FAKE_ROOT = """-----BEGIN CERTIFICATE-----
MIIBjTCCATOgAwIBAgIUKGSvHSZJlo4+7Ulv5I3kStfGGXYwCgYIKoZIzj0EAwIw
GzEZMBcGA1UEAwwQVGVzdCBSb290IChmYWtlKTAgFw0yNjExMTgyMTQ5NTNaGA8y
MTI2MTAyNTIxNDk1M1owGzEZMBcGA1UEAwwQVGVzdCBSb290IChmYWtlKTBZMBMG
ByqGSM49AgEGCCqGSM49AwEHA0IABJHgEFhWvKhlFqbSUohcGR+xYRihRTTeioh3
f+dH/5NT9A39ppG47fwkbVwUwNCch+3XFHVJIHKOjivCMrZzVzWjUzBRMB0GA1Ud
DgQWBBTrmn7hhMP6y0lPEJ1PXiLcgQlckzAfBgNVHSMEGDAWgBTrmn7hhMP6y0lP
EJ1PXiLcgQlckzAPBgNVHRMBAf8EBTADAQH/MAoGCCqGSM49BAMCA0gAMEUCIQCQ
iM+kQclZb/7J7YaqBX+rgTavkQXCxJ5FmZilxl76ngIgB+rI/VXiVPcvzttEmEX9
xbaKoOcN+cMcxiZkq/EyMZo=
-----END CERTIFICATE-----
"""
FAKE_LEAF = """-----BEGIN CERTIFICATE-----
MIIBsDCCAVagAwIBAgIUCTJPfhELVPc77kWonAWRjqhfXvYwCgYIKoZIzj0EAwIw
GzEZMBcGA1UEAwwQVGVzdCBSb290IChmYWtlKTAgFw0yNjExMTgyMTUwMDdaGA8y
MTI2MTAyNTIxNTAwN1owFDESMBAGA1UEAwwJbGVhZi50ZXN0MFkwEwYHKoZIzj0C
AQYIKoZIzj0DAQcDQgAE85YncFFLslLDxNUynn94Q6tvKbJYUzmzWrESmIFkVLQO
uDCjOTM4dHSQCKSeNfKOEsH6F6SV4/q9JvFW0rqIqKN9MHswOQYIKwYBBQUHAQEE
LTArMCkGCCsGAQUFBzAChh1odHRwOi8vYXR0YWNrZXIudGVzdC9yb290LmNydDAd
BgNVHQ4EFgQUgIGqSK4vBC61vpt7YxBi9zv3MgkwHwYDVR0jBBgwFoAU65p+4YTD
+stJTxCdT14i3IEJXJMwCgYIKoZIzj0EAwIDSAAwRQIgUw0qeU+lmnriEuKDxANA
FiVFoPyYBHgBHSzeCxkgA2YCIQD63C8IUjlnz2F1bn02gdldplqdSHqhQXWmUt8f
XC2T+w==
-----END CERTIFICATE-----
"""


def test_certificate_fallback_never_trusts_a_root_the_server_points_to(monkeypatch):
    """Security (2026-11-18): the fallback once loaded whatever the certificate's issuer link served, so a
    self-signed root from someone in the network path became trusted and the forged chain verified."""
    import ssl
    assert pr.is_self_signed(FAKE_ROOT) and not pr.is_self_signed(FAKE_LEAF)

    class Conn:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    class Tls(Conn):
        def getpeercert(self, binary_form=False): return ssl.PEM_cert_to_DER_cert(FAKE_LEAF)

    class Resp(Conn):
        def read(self, n): return FAKE_ROOT.encode()

    fetched = []
    monkeypatch.setattr(pr.socket, "create_connection", lambda addr, timeout=0: Conn())
    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", lambda self, sock, server_hostname=None: Tls())
    monkeypatch.setattr(pr.urllib.request, "urlopen", lambda req, timeout=0: fetched.append(req.full_url) or Resp())
    ctx = pr.context_with_issuer("leaf.test")
    assert fetched == ["http://attacker.test/root.crt"]
    assert not any("Test Root (fake)" in str(c.get("subject")) for c in ctx.get_ca_certs())
