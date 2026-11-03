"""The owners' admin accounts: creating them, removing them, and checking a login."""

import hashlib
from functools import cache

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AdminUser

# A passphrase of a few words clears this easily, and length is what makes a
# password hard to guess.
MIN_PASSWORD_LENGTH = 12

# Argon2id with pwdlib's recommended cost: deliberately slow (tens of
# milliseconds per check) and memory-hungry, so a stolen hash can't be
# guessed against at billions of tries a second.
password_hasher = PasswordHash.recommended()


class PasswordTooShort(ValueError):
    pass


class AdminNotFound(LookupError):
    pass


def set_password(session: Session, username: str, password: str) -> AdminUser:
    """Give the owner this password, creating their account if it doesn't exist yet.

    Changing the password also signs that owner out everywhere, because
    sessions are tied to the password (see session_stamp).
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordTooShort(f"use at least {MIN_PASSWORD_LENGTH} characters")

    admin = find(session, username)
    if admin is None:
        admin = AdminUser(username=username, password_hash="")
        session.add(admin)
    admin.password_hash = password_hasher.hash(password)
    session.commit()
    return admin


def remove(session: Session, username: str) -> None:
    """Delete the owner's account. Their open sessions stop working on their next request."""
    admin = find(session, username)
    if admin is None:
        raise AdminNotFound(username)
    session.delete(admin)
    session.commit()


def find(session: Session, username: str) -> AdminUser | None:
    return session.scalar(select(AdminUser).where(AdminUser.username == username))


def check_login(session: Session, username: str, password: str) -> AdminUser | None:
    """The account these credentials belong to, or None if they're wrong.

    An unknown username still pays for one hash check, against a throwaway
    hash. Otherwise a wrong username would answer in a millisecond and a
    wrong password in fifty, and the difference would tell an attacker which
    usernames exist.
    """
    admin = find(session, username)
    if admin is None:
        password_hasher.verify(password, _throwaway_hash())
        return None
    if not password_hasher.verify(password, admin.password_hash):
        return None
    return admin


def session_stamp(admin: AdminUser) -> str:
    """A short fingerprint of the owner's current password hash, kept in their session.

    A session only counts while its stamp matches, so a new password ends
    every session opened with the old one. The cookie is signed but readable,
    so it holds this digest rather than any part of the hash itself.
    """
    return hashlib.sha256(admin.password_hash.encode()).hexdigest()[:16]


@cache
def _throwaway_hash() -> str:
    return password_hasher.hash("not any owner's password")
