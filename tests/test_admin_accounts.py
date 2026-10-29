"""Owners' admin accounts: passwords, removal, and the commands that manage them."""

from collections.abc import Callable

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cli
from app.models import AdminUser
from app.services import admin_accounts

PASSWORD = "correct horse battery staple"


def test_the_password_is_stored_only_as_an_argon2_hash(session: Session) -> None:
    admin = admin_accounts.set_password(session, "owner", PASSWORD)

    assert PASSWORD not in admin.password_hash
    assert admin.password_hash.startswith("$argon2id$")


def test_a_short_password_is_refused(session: Session) -> None:
    with pytest.raises(admin_accounts.PasswordTooShort):
        admin_accounts.set_password(session, "owner", "short")

    assert admin_accounts.find(session, "owner") is None


def test_setting_a_password_again_replaces_it(session: Session) -> None:
    admin_accounts.set_password(session, "owner", PASSWORD)

    admin_accounts.set_password(session, "owner", "a completely different passphrase")

    assert admin_accounts.check_login(session, "owner", PASSWORD) is None
    assert admin_accounts.check_login(session, "owner", "a completely different passphrase")
    assert session.scalar(select(func.count()).select_from(AdminUser)) == 1


def test_check_login_rejects_an_unknown_username(session: Session) -> None:
    assert admin_accounts.check_login(session, "nobody", PASSWORD) is None


def test_removing_an_unknown_owner_is_an_error(session: Session) -> None:
    with pytest.raises(admin_accounts.AdminNotFound):
        admin_accounts.remove(session, "nobody")


def typed(*answers: str) -> Callable[[str], str]:
    """A stand-in for the password prompt that types these answers in order."""
    replies = iter(answers)
    return lambda _prompt: next(replies)


def test_cli_admin_password_creates_the_account(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(
        ["admin-password", "owner"],
        session_factory=lambda: session,
        read_password=typed(PASSWORD, PASSWORD),
    )

    assert exit_code == 0
    assert admin_accounts.check_login(session, "owner", PASSWORD) is not None
    assert PASSWORD not in capsys.readouterr().out


def test_cli_admin_password_refuses_a_mismatch(session: Session) -> None:
    exit_code = cli.main(
        ["admin-password", "owner"],
        session_factory=lambda: session,
        read_password=typed(PASSWORD, PASSWORD + "!"),
    )

    assert exit_code == 1
    assert admin_accounts.find(session, "owner") is None


def test_cli_admin_password_refuses_a_short_password(session: Session) -> None:
    exit_code = cli.main(
        ["admin-password", "owner"],
        session_factory=lambda: session,
        read_password=typed("short", "short"),
    )

    assert exit_code == 1
    assert admin_accounts.find(session, "owner") is None


def test_cli_admin_remove_deletes_the_account(session: Session) -> None:
    admin_accounts.set_password(session, "owner", PASSWORD)

    exit_code = cli.main(["admin-remove", "owner"], session_factory=lambda: session)

    assert exit_code == 0
    assert admin_accounts.find(session, "owner") is None


def test_cli_admin_remove_reports_an_unknown_owner(
    session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = cli.main(["admin-remove", "nobody"], session_factory=lambda: session)

    assert exit_code == 1
    assert "nobody" in capsys.readouterr().err
