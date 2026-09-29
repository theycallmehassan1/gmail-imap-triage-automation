# Gmail IMAP Triage Automation

A small Python utility, built on the [imapclient](https://imapclient.readthedocs.io/)
library, that connects to a Gmail account over IMAP and triages a folder
by message age, flagging and optionally archiving anything older than a
configurable threshold. Useful for a Spam or a large Inbox folder that
nobody is actively working through.

## Setup

Credentials are never hardcoded. Create a
[Gmail App Password](https://myaccount.google.com/apppasswords) (requires
2-Step Verification on the account) and set it as an environment variable:

```bash
export GMAIL_ADDRESS="you@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
pip install -r requirements.txt
```

An App Password can be revoked independently of the account password at
any time, which a hardcoded plaintext credential cannot offer.

## Usage

By default the script runs in dry-run mode and only reports what it
would do:

```bash
python3 imap_triage.py --folder "[Gmail]/Spam" --older-than-days 30
```

Add `--apply` to actually move the matched messages to the archive
folder:

```bash
python3 imap_triage.py --folder "[Gmail]/Spam" --older-than-days 30 --apply
```

Run `python3 imap_triage.py --help` for the full list of options
(host, folder, age threshold, and destination folder are all
configurable).

## License

Released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
