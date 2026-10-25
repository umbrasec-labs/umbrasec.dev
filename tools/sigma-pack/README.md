# sigma-pack


The detection rules and queries published in [UMBRASEC research writeups](https://umbrasec.dev/research/),
collected as runnable files. Honest status: **early** - this pack grows one writeup
at a time, and right now it contains exactly what the published writeups cover,
with one exception: the October 2026 LiteLLM release-compromise rules below shipped
ahead of their writeup because the indicators were too time-sensitive to sit on.
Nothing here claims to be more finished than it is.

Every rule ships with the context that makes it usable: the writeup explains the
technique, the log artifacts, the tuning knobs, and the false-positive profile.
Read the writeup before deploying the rule. Validate anything here yourself
before you run it - [sigma-cli](https://github.com/SigmaHQ/sigma-cli) will
syntax-check the whole directory:

```bash
sigma check tools/sigma-pack/rules/
```

## ATT&CK coverage

| Rule / query | Type | MITRE ATT&CK | Tactic | Status |
|---|---|---|---|---|
| [`kerberoasting-rc4-service-ticket.yml`](rules/windows/kerberoasting-rc4-service-ticket.yml) | Sigma | [T1558.003](https://attack.mitre.org/techniques/T1558/003/) Kerberoasting | Credential Access | experimental |
| [`kerberoasting-spn-fanout.yml`](rules/windows/kerberoasting-spn-fanout.yml) | Sigma (correlation) | [T1558.003](https://attack.mitre.org/techniques/T1558/003/) Kerberoasting | Credential Access | experimental |
| [`kerberoasting-honeypot-spn.yml`](rules/windows/kerberoasting-honeypot-spn.yml) | Sigma | [T1558.003](https://attack.mitre.org/techniques/T1558/003/) Kerberoasting | Credential Access | experimental |
| [`oauth-consent-sensitive-scopes.kql`](queries/kql/oauth-consent-sensitive-scopes.kql) | KQL | [T1528](https://attack.mitre.org/techniques/T1528/) Steal Application Access Token | Credential Access | query |
| [`oauth2-permission-grant-post.kql`](queries/kql/oauth2-permission-grant-post.kql) | KQL | [T1528](https://attack.mitre.org/techniques/T1528/) Steal Application Access Token | Credential Access | query |
| [`app-role-assignment.kql`](queries/kql/app-role-assignment.kql) | KQL | [T1528](https://attack.mitre.org/techniques/T1528/) Steal Application Access Token | Credential Access | query |
| [`app-credential-added.kql`](queries/kql/app-credential-added.kql) | KQL | [T1098.001](https://attack.mitre.org/techniques/T1098/001/) Additional Cloud Credentials | Persistence / Privilege Escalation | query |
| [`litellm-proxy-spawns-shell.yml`](rules/linux/litellm-proxy-spawns-shell.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App; [T1059](https://attack.mitre.org/techniques/T1059/) Command &amp; Scripting | Initial Access / Execution | experimental |
| [`litellm-mcp-test-endpoint.yml`](rules/web/litellm-mcp-test-endpoint.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App | Initial Access | experimental |
| [`litellm-stealer-files-linux.yml`](rules/linux/litellm-stealer-files-linux.yml) | Sigma | [T1195.002](https://attack.mitre.org/techniques/T1195/002/) Compromise Software Supply Chain; [T1546](https://attack.mitre.org/techniques/T1546/) Event Triggered Execution; [T1552](https://attack.mitre.org/techniques/T1552/) Unsecured Credentials | Initial Access / Persistence / Credential Access | experimental |
| [`litellm-stealer-files-windows.yml`](rules/windows/litellm-stealer-files-windows.yml) | Sigma | [T1195.002](https://attack.mitre.org/techniques/T1195/002/) Compromise Software Supply Chain; [T1546](https://attack.mitre.org/techniques/T1546/) Event Triggered Execution; [T1552](https://attack.mitre.org/techniques/T1552/) Unsecured Credentials | Initial Access / Persistence / Credential Access | experimental |
| [`litellm-stealer-exfil.yml`](rules/web/litellm-stealer-exfil.yml) | Sigma | [T1041](https://attack.mitre.org/techniques/T1041/) Exfiltration Over C2 Channel | Exfiltration | experimental |
| [`masquerading-svchost-outside-system32.yml`](rules/windows/masquerading-svchost-outside-system32.yml) | Sigma | [T1036.005](https://attack.mitre.org/techniques/T1036/005/) Match Legitimate Resource Name or Location | Stealth | experimental |
| [`cloudflared-tunnel-service-install.yml`](rules/windows/cloudflared-tunnel-service-install.yml) | Sigma | [T1543.003](https://attack.mitre.org/techniques/T1543/003/) Windows Service; [T1572](https://attack.mitre.org/techniques/T1572/) Protocol Tunneling | Persistence / Command &amp; Control | experimental |
| [`metabase-reset-password-sqli.yml`](rules/web/metabase-reset-password-sqli.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App | Initial Access | experimental |
| [`php-upload-progress-multipart-probe.yml`](rules/web/php-upload-progress-multipart-probe.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App | Initial Access | experimental |
| [`ransomware-inhibit-recovery-native-utilities.yml`](rules/windows/ransomware-inhibit-recovery-native-utilities.yml) | Sigma | [T1490](https://attack.mitre.org/techniques/T1490/) Inhibit System Recovery | Impact | experimental |
| [`defender-tamper-systemsettingsadminflows.yml`](rules/windows/defender-tamper-systemsettingsadminflows.yml) | Sigma | [T1685](https://attack.mitre.org/techniques/T1685/) Disable or Modify Tools | Defense Impairment | experimental |
| [`archiver-admin-share-collection.yml`](rules/windows/archiver-admin-share-collection.yml) | Sigma | [T1560.001](https://attack.mitre.org/techniques/T1560/001/) Archive via Utility; [T1039](https://attack.mitre.org/techniques/T1039/) Data from Network Shared Drive | Collection | experimental |
| [`rclone-transfer-to-remote.yml`](rules/windows/rclone-transfer-to-remote.yml) | Sigma | [T1567.002](https://attack.mitre.org/techniques/T1567/002/) Exfiltration to Cloud Storage | Exfiltration | experimental |
| [`remote-access-tool-service-install.yml`](rules/windows/remote-access-tool-service-install.yml) | Sigma | [T1219.002](https://attack.mitre.org/techniques/T1219/002/) Remote Desktop Software; [T1543.003](https://attack.mitre.org/techniques/T1543/003/) Windows Service | Command &amp; Control / Persistence | experimental |

`experimental` is the [Sigma status](https://sigmahq.io/docs/basics/rules.html) the
rules themselves declare - new rules, not yet battle-tested by many environments.
KQL queries are plain queries with no Sigma status.

## Contents

### Kerberoasting (MITRE ATT&CK T1558.003) - Sigma, Windows Security Event 4769

Writeup: [Detecting Kerberoasting: A Practical Walkthrough with Sigma](https://umbrasec.dev/research/detecting-kerberoasting.html)

| File | What it catches | Level |
|---|---|---|
| [`rules/windows/kerberoasting-rc4-service-ticket.yml`](rules/windows/kerberoasting-rc4-service-ticket.yml) | RC4 (0x17) service-ticket request in an AES-capable domain - the deliberate downgrade signal | medium |
| [`rules/windows/kerberoasting-spn-fanout.yml`](rules/windows/kerberoasting-spn-fanout.yml) | One account requesting tickets for many distinct SPNs in a short window (Sigma correlation rule) | medium |
| [`rules/windows/kerberoasting-honeypot-spn.yml`](rules/windows/kerberoasting-honeypot-spn.yml) | Any ticket request naming your decoy SPN account - edit the `ServiceName` to your decoy first | high |

Prerequisite: *Audit Kerberos Service Ticket Operations* (Success) enabled on all
domain controllers, Security log shipped from every DC.

### OAuth consent phishing (MITRE ATT&CK T1528, follow-on T1098.001) - KQL, Microsoft Sentinel / Log Analytics

Writeup: [Detecting OAuth Consent Phishing in Microsoft 365](https://umbrasec.dev/research/detecting-oauth-consent-phishing.html)

| File | What it catches |
|---|---|
| [`queries/kql/oauth-consent-sensitive-scopes.kql`](queries/kql/oauth-consent-sensitive-scopes.kql) | "Consent to application" audit events granting mail/files/directory scopes |
| [`queries/kql/oauth2-permission-grant-post.kql`](queries/kql/oauth2-permission-grant-post.kql) | The Graph API POST that creates a delegated permission grant (highest fidelity) |
| [`queries/kql/app-role-assignment.kql`](queries/kql/app-role-assignment.kql) | App-only (application permission) role assignments - standing access |
| [`queries/kql/app-credential-added.kql`](queries/kql/app-credential-added.kql) | Follow-on persistence (T1098.001): a new client secret or certificate on an application or service principal |

Prerequisite: Entra ID `AuditLogs` and `MicrosoftGraphActivityLogs` flowing into
your workspace. The shape of `modifiedProperties` shifts between schema versions -
validate field names against your own tenant before you alert on anything.

### LiteLLM command injection - CVE-2026-42271 (MITRE ATT&CK T1190 / T1059)

Writeup: [Detecting the LiteLLM Command Injection (CVE-2026-42271) in Your AI Gateway](https://umbrasec.dev/research/detecting-litellm-command-injection.html)

| File | What it catches | Level |
|---|---|---|
| [`rules/linux/litellm-proxy-spawns-shell.yml`](rules/linux/litellm-proxy-spawns-shell.yml) | The LiteLLM proxy process spawning a shell or recon/download utility - the command-injection landing (high fidelity). Covers versioned interpreters (`python3.7` to `python3.14`), `nc.openbsd` / `nc.traditional` / `netcat` and `busybox` | high |
| [`rules/web/litellm-mcp-test-endpoint.yml`](rules/web/litellm-mcp-test-endpoint.yml) | POST requests to the vulnerable MCP preview endpoints (`/mcp-rest/test/connection`, `/mcp-rest/test/tools/list`) - the front-door signal | medium |

Prerequisite: for the host rule, Linux process-creation telemetry (Auditd execve,
Sysmon for Linux, or EDR) from the LiteLLM host/container; for the web rule, HTTP
access logs from the reverse proxy / ingress in front of LiteLLM. Scope the host
rule to your LiteLLM hosts to cut generic `python` parent noise. Patch status is
the real control - these cover the window before you've patched and the assets you
haven't found yet.

### LiteLLM release compromise - 1.107.0, 21 October 2026 (MITRE ATT&CK T1195.002 / T1546 / T1552 / T1041)

Writeup: pending. Until it lands, the sources are LiteLLM's
[incident post](https://docs.litellm.ai/blog/security-incident-oct-21-2026) and
Wiz's [analysis](https://www.wiz.io/blog/litellm-compromised-steals-credentials),
which is where the indicators below come from.

The June rules above cover a command injection *in* the LiteLLM proxy. On 21
October 2026 the project's own release pipeline was hijacked: stolen developer
GitHub CLI tokens, branch protection overridden, and the releaser pointed at a
lookalike repository (`Berri-AI`, not `BerriAI`). `litellm==1.107.0` shipped a
credential stealer to PyPI (live 11:39-13:23 UTC) and to the `v1.107.0`, `latest`,
`main-latest` and `main-stable` Docker/GHCR tags. 1.106.2 is the last clean
release. LiteLLM suspects the tokens were lifted from the logs of its own
internet-exposed deployment through a recently patched vulnerability it has not
named.

| Rule | What it catches | Level |
|---|---|---|
| [`rules/linux/litellm-stealer-files-linux.yml`](rules/linux/litellm-stealer-files-linux.yml) | `cook.pth` / `cook.py` landing in a `site-packages` or `dist-packages` root, or the compiled `cook.*.pyc` - 1.107.0 was installed. Files under `/tmp/.pc_sq_*` / `/tmp/.pc_e_*`, the `/tmp/.pc_once_72129118c59f5636c0bb` run-once marker or `/tmp/remote_code_loader.lock` - it ran | high |
| [`rules/windows/litellm-stealer-files-windows.yml`](rules/windows/litellm-stealer-files-windows.yml) | The same `cook.pth` / `cook.py` / `.pyc` drop on Windows. Files under `.pc_sq_*` / `.pc_e_*` in the temp folder, or the `\tmp\.pc_once_72129118c59f5636c0bb` marker on the few hosts where a `\tmp` directory exists - it ran | high |
| [`rules/web/litellm-stealer-exfil.yml`](rules/web/litellm-stealer-exfil.yml) | Any request to `litellm.dev` (lookalike; the real domains are `litellm.ai` / `docs.litellm.ai`), including hosts logged with a port or a trailing dot - the stealer POSTs to `www.litellm.dev/healthcheck` with a hardcoded `X-Token` header | high |

Prerequisite: file-creation telemetry (Sysmon Event 11 on either platform, auditd,
or EDR) from hosts that run Python, and proxy logs that retain the destination
host (DNS logs work for a manual hunt on `litellm.dev`, not for the rule). No path
is anchored to the start on purpose (each is a suffix or substring match): virtualenvs,
conda, Debian's `dist-packages` and containers all put the files somewhere different, and a sensor on a Docker or
Kubernetes node sees a container's `/tmp` under the overlay or rootfs path.

**Hunt, not a rule - the stolen keys get used.** Treat any host that started Python
with 1.107.0 and had outbound internet as breached. Wiz saw the stealer take the
instance role via IMDS, the process environment, `~/.aws` and up to 500 rows of
`LiteLLM_CredentialsTable`. LiteLLM's rotation list is wider - treat the instance or
task IAM role, every provider key in the proxy database, master and virtual keys,
`DATABASE_URL` and every secret in the environment of any process on the host as
taken. Wiz watched stolen instance-role credentials get validated about 4.5 hours after
exfiltration: `sts:GetCallerIdentity`, then `bedrock:ListFoundationModels` (the
LLMjacking tell), in some accounts followed by `iam:ListRoles`, `ListUsers` and
`ListAccessKeys`. Hunt CloudTrail for `GetCallerIdentity` by your instance roles
from a source IP outside your own ranges, and for Bedrock model listing by a role
that never touched Bedrock before. The IPs Wiz saw (`168.100.8[.]57`,
`165.227.201[.]8`) are already stale; the sequence is the signal.

Remediation order matters. Start rotating everything listed above immediately -
it is already gone, and the stolen keys were in use within hours. In parallel,
and without running `pip` or Python on the host first (any Python start reruns
the payload), delete the dropped files from a shell, kill the daemon holding
`/tmp/remote_code_loader.lock`, then rebuild images and virtualenvs from scratch
pinned to `litellm==1.106.2`.

### N-able N-central intrusion artifacts - CVE-2026-18556 / CVE-2026-18577 (T1036.005, T1543.003, T1572)

Writeup: [Your MSP's RMM Is Your Attack Surface](https://umbrasec.dev/research/n-able-ncentral-msp-supply-chain.html)

These two rules do not detect the N-central authentication bypass itself - that
happens on the MSP's server, not on your endpoints. They detect what the
operators did *after* it, on the managed machines, which is the part a managed
client can actually see.

| Rule | What it catches | Level |
|---|---|---|
| [`rules/windows/masquerading-svchost-outside-system32.yml`](rules/windows/masquerading-svchost-outside-system32.yml) | A binary named `svchost.exe` running from anywhere other than System32/SysWOW64/WinSxS - the Documents-folder drop reported by N-able is one instance | high |
| [`rules/windows/cloudflared-tunnel-service-install.yml`](rules/windows/cloudflared-tunnel-service-install.yml) | Registration of a `Cloudflared` service, used here to hold access after N-central credentials were revoked | medium |

Prerequisite: Windows process-creation telemetry (Sysmon Event 1 or Security
4688 with command line auditing) for the first rule, and the Windows System log
(Event 7045) for the second.

Read the [writeup](https://umbrasec.dev/research/n-able-ncentral-msp-supply-chain.html)
before deploying - the Cloudflare Tunnel rule in particular is a tuning
exercise, not a drop-in alert.

### Metabase unauthenticated SQL injection - CVE-2026-72898 (MITRE ATT&CK T1190)

Writeup: [Sixteen Days From KEV to Exfiltration](https://umbrasec.dev/research/mathspace-metabase-internal-tooling.html)

| Rule | What it catches | Level |
|---|---|---|
| [`rules/web/metabase-reset-password-sqli.yml`](rules/web/metabase-reset-password-sqli.yml) | SQL metacharacters, literal or percent-encoded, in a request to Metabase's unauthenticated `/api/session/reset_password` endpoint - the front-door signal | high |

Prerequisite: web server, reverse proxy or WAF logs for the Metabase host, with
the request line retained. A payload carried in the POST body is invisible to
webserver-category logs, so pair this with body capture where you have it, and
with the volume hunt in the writeup. Patching (58.24, 59.21, 60.17, 61.11, 62.9,
63.5) and blocking the endpoint are the real controls; this covers the window
before you got there.

### php2shell request-side tripwire - CVE-2026-109619 (MITRE ATT&CK T1190)

Writeup: [php2shell and the Hallucinated Exploit](https://umbrasec.dev/research/php2shell-hallucinated-exploits.html)

| Rule | What it catches | Level |
|---|---|---|
| [`rules/web/php-upload-progress-multipart-probe.yml`](rules/web/php-upload-progress-multipart-probe.yml) | A multipart/form-data request carrying `PHP_SESSION_UPLOAD_PROGRESS`, the field the CVE-2026-109619 session-lifecycle case uses - and also the 2018 session-poisoning trick, scanners and fake PoCs. Exposure and attention, not compromise | low |

Prerequisite: a WAF or reverse proxy that logs request bodies and the
Content-Type header. `cs-request-body` and `cs-content-type` are not in the Sigma
webserver taxonomy, so map them to your fields in the conversion pipeline or the
query never matches. Confirm how much of a body your WAF inspects and logs: the
field can sit past the limit. The rule does not cover the CVE's other paths or
CVE-2026-109618; the worker-crash hunt in the writeup is the stronger signal.
The hunt stays in the writeup rather than the pack: it looks for a burst of PHP
worker crashes against each host's normal rate, timed against hits from this
rule, which a single-event Sigma rule does not express.

### Ransomware staging, recovery inhibition, Defender tampering and remote access tools - SafePay and INC Ransom (T1490, T1685, T1560.001, T1039, T1567.002, T1219.002, T1543.003)

Writeups: [SafePay Is Claiming Australian Victims](https://umbrasec.dev/research/safepay-australian-smb.html)
and [How INC Ransom Hits Australian Organisations](https://umbrasec.dev/research/inc-ransom-australian-smb.html)

The recovery rule comes from the SafePay writeup, the Defender rule from the INC
writeup, and the archiver, rclone and remote access tool rules from both. None of
them is specific to one crew: they catch the native-tool and commodity-tool steps
many ransomware operators share, so a match says "look now", not "this is SafePay".

| Rule | What it catches | Level |
|---|---|---|
| [`rules/windows/ransomware-inhibit-recovery-native-utilities.yml`](rules/windows/ransomware-inhibit-recovery-native-utilities.yml) | `vssadmin` / `wmic` deleting shadow copies, `wbadmin delete catalog`, or `bcdedit` set to ignore boot failures or to disable automatic recovery - including renamed copies of the utilities | high |
| [`rules/windows/defender-tamper-systemsettingsadminflows.yml`](rules/windows/defender-tamper-systemsettingsadminflows.yml) | `SystemSettingsAdminFlows.exe` run with a Defender argument by anything other than the Settings app - the INC Ransom Defender switch-off Huntress documented | medium |
| [`rules/windows/archiver-admin-share-collection.yml`](rules/windows/archiver-admin-share-collection.yml) | WinRAR, RAR or 7-Zip creating or adding to an archive with a `C$` to `F$` admin share on the command line | medium |
| [`rules/windows/rclone-transfer-to-remote.yml`](rules/windows/rclone-transfer-to-remote.yml) | rclone, renamed or not, started with a command that writes to a destination (`copy`, `sync`, `move`, `rcat`, `archive create` and the rest) | medium |
| [`rules/windows/remote-access-tool-service-install.yml`](rules/windows/remote-access-tool-service-install.yml) | A Windows service registered for ScreenConnect, AnyDesk, TeamViewer, SimpleHelp, Mesh Agent or RustDesk (System event 7045), matched on a documented default path or name (for ScreenConnect, from Microsoft's analysis of a malicious install). One edit point: put a string unique to your own sanctioned instance in `filter_sanctioned_rmm` - until you do, it fires on every install. Only ScreenConnect and custom AnyDesk clients have such a string in the event | medium |

Prerequisite: Windows process-creation telemetry with command lines (Sysmon
Event 1, or EDR) for the first four rules, and the Windows System log (Event 7045)
for the remote access tool rule. Security event 4688 works for the image-name and
command-line parts, but it carries no PE metadata (`OriginalFileName`, `Product`,
`Description`), so renamed binaries get through. Pair the Defender rule with
event 5007 from the Defender Operational log to see which setting changed. The
four process rules see command lines only: shadow copies deleted through the VSS
API, rclone driven through `rcd` or `serve`, and an archive built from a mapped
drive are all blind spots the rule files list in full. FileZilla, which the
SafePay reports name for exfiltration, is not covered because the reports used
publish no FileZilla command line or destination to build a rule on; INC's
MEGAsync and Restic are not covered either. The remote access tool rule cannot see a portable run (no service
is created), a renamed service in an unrelated folder, a tool it does not list, or
abuse of your own sanctioned instance.

## How to use these

1. Read the writeup for the rule you're deploying.
2. Run the rule in **report-only mode** first and baseline your environment.
3. Tune per the notes in each file (thresholds, allowlists, the honeypot account name).
4. Only then page anyone with it.

Sigma rules convert to your SIEM's query language with
[sigma-cli / pySigma](https://github.com/SigmaHQ/sigma-cli).

## A rule misbehaved?

That's exactly the feedback this project wants -
[open an issue](https://github.com/umbrasec-labs/umbrasec.dev/issues). Corrections are credited.

License: MIT, same as the rest of the repo's code.
