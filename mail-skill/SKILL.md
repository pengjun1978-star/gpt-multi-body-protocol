# 霍普智联企业 Mail Skill v1.1.1

Declared capabilities: `enterprise_mail.search/read/thread/send/reply/forward`, `attachments.list/download/parse`, `identity`, `idempotency`, `receipt`, `callback`.

Every operation must report `SUCCESS`, `RETRYABLE`, `BLOCKED`, or `FAILED`. Credentials are read from macOS Keychain service `codex-hypcloud-email`; never commit them.

Install this directory into the employee Skills directory, configure the local mailbox, then run `health-check` and `self-test`. Self-test is dry-run until an authorized test mailbox is configured.
