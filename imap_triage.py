#!/usr/bin/env python3
"""
Gmail IMAP Triage Automation

A small utility that connects to a Gmail account over IMAP and applies
a simple triage rule to a folder: flag messages older than a threshold
and move them to Archive, so an inbox or a folder like Spam doesn't
accumulate indefinitely without anyone acting on it.

Credentials are never hardcoded. Set them as environment variables:

    export GMAIL_ADDRESS="you@gmail.com"
    export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"   # a Gmail App Password, not your account password
    python3 imap_triage.py --folder "[Gmail]/Spam" --older-than-days 30 --dry-run

Gmail App Passwords require 2-Step Verification to be enabled on the
account, and are created at https://myaccount.google.com/apppasswords.
An App Password can be revoked independently of the account password
if this script, or the environment it runs in, is ever compromised,
which a hardcoded plaintext password cannot offer.

By default this runs in --dry-run mode and only reports what it would
do. Pass --apply to actually move messages.
"""

import argparse
import email.utils
import os
import sys
from datetime import datetime, timedelta, timezone

from imapclient import IMAPClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage an IMAP folder by age.")
    parser.add_argument("--host", default="imap.gmail.com", help="IMAP host (default: imap.gmail.com)")
    parser.add_argument("--folder", default="[Gmail]/Spam", help="Folder to triage (default: [Gmail]/Spam)")
    parser.add_argument("--older-than-days", type=int, default=30, help="Archive messages older than this many days (default: 30)")
    parser.add_argument("--archive-folder", default="[Gmail]/All Mail", help="Destination folder (default: [Gmail]/All Mail)")
    parser.add_argument("--apply", action="store_true", help="Actually move messages. Without this flag, only reports what would happen.")
    return parser.parse_args()


def get_credentials() -> tuple[str, str]:
    address = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not address or not app_password:
        print(
            "Error: set GMAIL_ADDRESS and GMAIL_APP_PASSWORD as environment variables.\n"
            "Use a Gmail App Password (https://myaccount.google.com/apppasswords), never your real account password.",
            file=sys.stderr,
        )
        sys.exit(1)
    return address, app_password


def run(host: str, folder: str, older_than_days: int, archive_folder: str, apply: bool) -> int:
    address, app_password = get_credentials()
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)

    with IMAPClient(host=host) as client:
        client.login(address, app_password)
        client.select_folder(folder)

        message_ids = client.search(["NOT", "DELETED"])
        if not message_ids:
            print(f"No messages in {folder!r}.")
            return 0

        envelopes = client.fetch(message_ids, ["ENVELOPE"])
        to_archive = []
        for msg_id, data in envelopes.items():
            envelope = data[b"ENVELOPE"]
            sent_at = envelope.date
            if sent_at is None:
                continue
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=timezone.utc)
            if sent_at < cutoff:
                to_archive.append((msg_id, envelope.subject, sent_at))

        print(f"{len(to_archive)} of {len(message_ids)} message(s) in {folder!r} are older than {older_than_days} days.")
        for msg_id, subject, sent_at in to_archive:
            subject_text = subject.decode(errors="replace") if subject else "(no subject)"
            print(f"  [{msg_id}] {sent_at.date()}  {subject_text[:80]}")

        if not to_archive:
            return 0

        if apply:
            ids = [msg_id for msg_id, _, _ in to_archive]
            client.move(ids, archive_folder)
            print(f"Moved {len(ids)} message(s) to {archive_folder!r}.")
        else:
            print("\nDry run only, no messages were moved. Re-run with --apply to move them.")

    return 0


def main() -> int:
    args = parse_args()
    return run(args.host, args.folder, args.older_than_days, args.archive_folder, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
