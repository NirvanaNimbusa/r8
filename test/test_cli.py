import shlex
import subprocess
from pathlib import Path

import pytest
import r8.cli
from click.testing import CliRunner

here: Path = Path(__file__).parent


@pytest.fixture(scope="module")
def r8cli():
    runner = CliRunner()

    def run(command, *args, **kwargs):
        kwargs.setdefault("catch_exceptions", False)
        result = runner.invoke(r8.cli.main, command, *args, **kwargs)
        if result.exit_code != 0:
            raise RuntimeError(result.output)
        return result

    with runner.isolated_filesystem():
        run("sql init --origin http://localhost:8000")
        run(["sql", "file", "--no-backup", str((here / "test.sql").absolute())])
        yield run


def test_challenges(r8cli):
    assert "FormExample" in r8cli("challenges list-available").output
    assert "Attendance(active)" in r8cli("challenges list").output


def test_events(r8cli):
    r8cli("events --no-watch")


def test_flags(r8cli):
    r8cli("flags create Attendance(active) foo")
    r8cli("flags submit foo user1")
    r8cli("flags limit foo")
    with pytest.raises(RuntimeError, match='Revoke all submissions first'):
        r8cli("flags delete foo")
    r8cli("flags list")

    r8cli("flags revoke --no-backup foo user1")
    r8cli("flags delete foo")


def test_password(r8cli):
    assert "$argon2id$" in r8cli("password generate").output
    assert "$argon2id$" in r8cli("password hash --password foo").output


def test_settings(r8cli):
    r8cli("settings set foo foobar")
    assert "foobar" in r8cli("settings view").output
    r8cli("settings delete foo")
    assert "foobar" not in r8cli("settings view").output


def test_sql(r8cli):
    r8cli("sql stmt --no-backup SELECT 1")
    r8cli("sql tables")


def test_users(r8cli):
    r8cli("users")
    r8cli("users -T --teams --format csv")