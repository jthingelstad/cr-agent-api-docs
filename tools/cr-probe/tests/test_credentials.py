"""Credential discovery must identify a key by what it IS, not what it is called."""

import base64
import json

from crprobe.credentials import Candidate, discover


def _fake_jwt(payload: dict) -> str:
    def seg(obj):
        raw = json.dumps(obj).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")
    # The signature must still be valid base64url even though nothing verifies
    # it -- PyJWT decodes all three segments before it decides to skip checking.
    fake_sig = base64.urlsafe_b64encode(b"not-a-real-signature").decode().rstrip("=")
    return f"{seg({'alg': 'HS512', 'typ': 'JWT'})}.{seg(payload)}.{fake_sig}"


SUPERCELL = _fake_jwt({"iss": "supercell", "aud": "supercell:gameapi",
                       "limits": [{"cidrs": ["203.0.113.7/32"], "type": "client"}]})
OTHER_SERVICE = _fake_jwt({"iss": "some-other-issuer", "sub": "abc"})


def test_finds_key_under_an_unexpected_variable_name(tmp_path):
    """The whole point: point it at any file and it works out which value is the key."""
    env = tmp_path / ".env"
    env.write_text(f"TOTALLY_UNRELATED_NAME={SUPERCELL}\nDEBUG=true\n")

    found = discover((str(env),))

    assert [c.name for c in found] == ["TOTALLY_UNRELATED_NAME"]
    assert found[0].looks_supercell


def test_ignores_jwts_from_other_services(tmp_path):
    env = tmp_path / ".env"
    env.write_text(f"SESSION_JWT={OTHER_SERVICE}\n")

    assert discover((str(env),)) == []


def test_ignores_other_providers_secrets_by_name(tmp_path):
    """A .env is a junk drawer; probing AWS keys wastes calls and buries the answer."""
    env = tmp_path / ".env"
    env.write_text("AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG\nGITHUB_TOKEN=ghp_xxx\n")

    assert discover((str(env),)) == []


def test_supercell_keys_sort_before_weaker_guesses(tmp_path):
    env = tmp_path / ".env"
    env.write_text(f"CR_API_KEY=not-a-jwt-just-a-name-match\nSOMETHING={SUPERCELL}\n")

    found = discover((str(env),))

    assert found[0].name == "SOMETHING", "a positively identified key must be tried first"


def test_reads_a_file_that_is_only_the_token(tmp_path):
    bare = tmp_path / "token.txt"
    bare.write_text(f"  {SUPERCELL}  \n")

    found = discover((str(bare),))

    assert len(found) == 1
    assert found[0].name == "(file contents)"


def test_key_name_narrows_to_one_variable(tmp_path):
    env = tmp_path / ".env"
    env.write_text(f"FIRST={SUPERCELL}\nSECOND={SUPERCELL[:-1]}x\n")

    found = discover((str(env),), name="SECOND")

    assert [c.name for c in found] == ["SECOND"]


def test_allowlist_is_extracted_and_compared():
    candidate = Candidate("t/.env", "K", SUPERCELL, json.loads(
        base64.urlsafe_b64decode(SUPERCELL.split(".")[1] + "==").decode()))

    assert candidate.allowed_cidrs == ["203.0.113.7/32"]
    assert candidate.permits_ip("203.0.113.7") is True
    assert candidate.permits_ip("198.51.100.9") is False
    assert candidate.permits_ip(None) is None, "unknown IP must not be reported as a mismatch"


def test_label_never_exposes_the_value():
    candidate = Candidate("elixir-mcp/.env", "CR_API_TOKEN", SUPERCELL)

    assert candidate.label == "elixir-mcp/.env:CR_API_TOKEN"
    assert SUPERCELL not in repr(candidate)
