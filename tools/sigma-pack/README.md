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
| [`metabase-egress-inversion.kql`](queries/kql/metabase-egress-inversion.kql) | KQL | [T1567](https://attack.mitre.org/techniques/T1567/) Exfiltration Over Web Service | Exfiltration | query |
| [`litellm-proxy-spawns-shell.yml`](rules/linux/litellm-proxy-spawns-shell.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App; [T1059](https://attack.mitre.org/techniques/T1059/) Command &amp; Scripting | Initial Access / Execution | experimental |
| [`litellm-mcp-test-endpoint.yml`](rules/web/litellm-mcp-test-endpoint.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App | Initial Access | experimental |
| [`litellm-stealer-files-linux.yml`](rules/linux/litellm-stealer-files-linux.yml) | Sigma | [T1195.002](https://attack.mitre.org/techniques/T1195/002/) Compromise Software Supply Chain; [T1546](https://attack.mitre.org/techniques/T1546/) Event Triggered Execution; [T1552](https://attack.mitre.org/techniques/T1552/) Unsecured Credentials | Initial Access / Persistence / Credential Access | experimental |
| [`litellm-stealer-files-windows.yml`](rules/windows/litellm-stealer-files-windows.yml) | Sigma | [T1195.002](https://attack.mitre.org/techniques/T1195/002/) Compromise Software Supply Chain; [T1546](https://attack.mitre.org/techniques/T1546/) Event Triggered Execution; [T1552](https://attack.mitre.org/techniques/T1552/) Unsecured Credentials | Initial Access / Persistence / Credential Access | experimental |
| [`litellm-stealer-exfil.yml`](rules/web/litellm-stealer-exfil.yml) | Sigma | [T1041](https://attack.mitre.org/techniques/T1041/) Exfiltration Over C2 Channel | Exfiltration | experimental |
| [`masquerading-svchost-outside-system32.yml`](rules/windows/masquerading-svchost-outside-system32.yml) | Sigma | [T1036.005](https://attack.mitre.org/techniques/T1036/005/) Match Legitimate Resource Name or Location | Stealth | experimental |
| [`cloudflared-tunnel-service-install.yml`](rules/windows/cloudflared-tunnel-service-install.yml) | Sigma | [T1543.003](https://attack.mitre.org/techniques/T1543/003/) Windows Service; [T1572](https://attack.mitre.org/techniques/T1572/) Protocol Tunneling | Persistence / Command &amp; Control | experimental |
| [`metabase-reset-password-sqli.yml`](rules/web/metabase-reset-password-sqli.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App | Initial Access | experimental |
| [`metabase-reset-password-burst.yml`](rules/web/metabase-reset-password-burst.yml) | Sigma (correlation) | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App | Initial Access | experimental |
| [`php-upload-progress-multipart-probe.yml`](rules/web/php-upload-progress-multipart-probe.yml) | Sigma | [T1190](https://attack.mitre.org/techniques/T1190/) Exploit Public-Facing App | Initial Access | experimental |
| [`ransomware-inhibit-recovery-native-utilities.yml`](rules/windows/ransomware-inhibit-recovery-native-utilities.yml) | Sigma | [T1490](https://attack.mitre.org/techniques/T1490/) Inhibit System Recovery | Impact | experimental |
| [`defender-tamper-systemsettingsadminflows.yml`](rules/windows/defender-tamper-systemsettingsadminflows.yml) | Sigma | [T1685](https://attack.mitre.org/techniques/T1685/) Disable or Modify Tools | Defense Impairment | experimental |
| [`archiver-admin-share-collection.yml`](rules/windows/archiver-admin-share-collection.yml) | Sigma | [T1560.001](https://attack.mitre.org/techniques/T1560/001/) Archive via Utility; [T1039](https://attack.mitre.org/techniques/T1039/) Data from Network Shared Drive | Collection | experimental |
| [`rclone-transfer-to-remote.yml`](rules/windows/rclone-transfer-to-remote.yml) | Sigma | [T1567.002](https://attack.mitre.org/techniques/T1567/002/) Exfiltration to Cloud Storage | Exfiltration | experimental |
| [`remote-access-tool-service-install.yml`](rules/windows/remote-access-tool-service-install.yml) | Sigma | [T1219.002](https://attack.mitre.org/techniques/T1219/002/) Remote Desktop Software; [T1543.003](https://attack.mitre.org/techniques/T1543/003/) Windows Service | Command &amp; Control / Persistence | experimental |
| [`ai-agent-cli-headless-approval-bypass.yml`](rules/cross-platform/ai-agent-cli-headless-approval-bypass.yml) | Sigma | [T1059](https://attack.mitre.org/techniques/T1059/) Command &amp; Scripting | Execution | experimental |
| [`ai-agent-shell-risky-command.yml`](rules/cross-platform/ai-agent-shell-risky-command.yml) | Sigma | [T1059](https://attack.mitre.org/techniques/T1059/) Command &amp; Scripting; [T1698](https://attack.mitre.org/techniques/T1698/) Indirect Prompt Injection; [T1552.001](https://attack.mitre.org/techniques/T1552/001/) Credentials In Files; [T1105](https://attack.mitre.org/techniques/T1105/) Ingress Tool Transfer | Execution / Credential Access / Command &amp; Control | experimental |
| [`all-agent-shells-risky-command.kql`](queries/kql/all-agent-shells-risky-command.kql) | KQL | [T1059](https://attack.mitre.org/techniques/T1059/) Command &amp; Scripting; [T1552.001](https://attack.mitre.org/techniques/T1552/001/) Credentials In Files; [T1105](https://attack.mitre.org/techniques/T1105/) Ingress Tool Transfer | Execution / Credential Access / Command &amp; Control | query |
| [`ai-agent-config-changed-by-command.yml`](rules/cross-platform/ai-agent-config-changed-by-command.yml) | Sigma | [T1546](https://attack.mitre.org/techniques/T1546/) Event Triggered Execution; [T1698](https://attack.mitre.org/techniques/T1698/) Indirect Prompt Injection | Persistence / Execution | experimental |
| [`ai-agent-config-new-file.yml`](rules/cross-platform/ai-agent-config-new-file.yml) | Sigma | [T1546](https://attack.mitre.org/techniques/T1546/) Event Triggered Execution; [T1195.002](https://attack.mitre.org/techniques/T1195/002/) Compromise Software Supply Chain | Persistence / Initial Access | experimental |
| [`ai-agent-config-file-writes.kql`](queries/kql/ai-agent-config-file-writes.kql) | KQL | [T1546](https://attack.mitre.org/techniques/T1546/) Event Triggered Execution; [T1195.002](https://attack.mitre.org/techniques/T1195/002/) Compromise Software Supply Chain | Persistence / Initial Access | query |

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

### Metabase unauthenticated SQL injection - CVE-2026-72898 (MITRE ATT&CK T1190, T1567)

Writeup: [Sixteen Days From KEV to Exfiltration](https://umbrasec.dev/research/mathspace-metabase-internal-tooling.html)

| Rule | What it catches | Level |
|---|---|---|
| [`rules/web/metabase-reset-password-sqli.yml`](rules/web/metabase-reset-password-sqli.yml) | SQL metacharacters, literal or percent-encoded, in a request to Metabase's unauthenticated `/api/session/reset_password` endpoint - the front-door signal | high |
| [`rules/web/metabase-reset-password-burst.yml`](rules/web/metabase-reset-password-burst.yml) | Ten or more requests to the same endpoint from one client address in ten minutes (Sigma correlation rule). Payload-blind, so it also counts an exploit carried in the POST body | medium |
| [`queries/kql/metabase-egress-inversion.kql`](queries/kql/metabase-egress-inversion.kql) | KQL over firewall logs (`CommonSecurityLog`): a day's outbound bytes from the Metabase host at a multiple of its own 14-day median - the bulk-extraction signal | query |

Prerequisite: web server, reverse proxy or WAF logs for the Metabase host, with
the request line retained. A payload carried in the POST body is invisible to
webserver-category logs, so pair the markers rule with body capture where you
have it, and with the burst rule, which counts requests and reads no payload. The
burst rule groups by `c-ip`: if a proxy logs its own address there, log the
forwarded client address first. The egress query needs firewall logs that carry
the Metabase host's (and its reverse proxy's) address and byte counts; check once
which end of a session `SentBytes` counts from on your firewall, because
Microsoft does not document it. An extraction split across days so no single day
reaches the multiple (T1030) stays under it. Patching (58.24, 59.21, 60.17, 61.11, 62.9,
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
| [`rules/windows/ransomware-inhibit-recovery-native-utilities.yml`](rules/windows/ransomware-inhibit-recovery-native-utilities.yml) | `vssadmin` / `wmic` deleting shadow copies, `wbadmin delete catalog`, `delete backup` or `delete systemstatebackup`, or `bcdedit` set to ignore boot failures or to disable automatic recovery - including renamed copies of the utilities | high |
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

### Hijacked AI coding agents (MITRE ATT&CK T1059 / T1698 / T1552.001 / T1105) - Sigma, process creation on Windows, macOS and Linux; KQL, Microsoft Defender XDR

Writeup: [What a Hijacked AI Coding Agent Leaves in Your Logs](https://umbrasec.dev/research/detecting-hijacked-ai-coding-agents.html)

| Rule | What it catches | Level |
|---|---|---|
| [`rules/cross-platform/ai-agent-cli-headless-approval-bypass.yml`](rules/cross-platform/ai-agent-cli-headless-approval-bypass.yml) | Claude Code, Gemini CLI, Codex CLI, GitHub Copilot CLI, Amazon Q Developer CLI, Cursor CLI or Devin CLI started headless with its permission prompts switched off - the shape of the Nx "s1ngularity" packages and Amazon Q for VS Code 1.84.0 (CVE-2025-8217). Codex is matched on `--dangerously-bypass-approvals-and-sandbox` and its `--yolo` alias; Copilot also on a bare `--allow-tool` shell grant, with `-p` last or `--acp` as headless markers; the Cursor CLI (node from a `cursor-agent` folder) on `--force`, `-f` or `--yolo` with no headless flag; the Devin CLI on `--permission-mode dangerous`, `yolo` or `bypass`. A Copilot run with only `--allow-all-tools` or `COPILOT_ALLOW_ALL`, Cursor's `approvalMode` config, `DEVIN_PERMISSION_MODE`, Gemini's `-y` under node and a Gemini positional prompt are not covered | high |
| [`rules/cross-platform/ai-agent-shell-risky-command.yml`](rules/cross-platform/ai-agent-shell-risky-command.yml) | A shell started by a coding agent (Claude Code, Codex, Kilo Code, Amazon Q Developer CLI, GitHub Copilot CLI or a `cursor-agent` folder process as parent; Claude Code, Gemini CLI, Kilo Code, Copilot CLI, Cursor Git Bash or legacy Windsurf Cascade wrapper on the command line; a Cursor CLI or IDE agent wrapper on the parent command line; or any VS Code extension spawning a shell directly from the extension host) that names a credential file or token source, pipes a download into an interpreter, runs a download through command substitution, or builds a DNS lookup from a command substitution. A `.env` read, a download saved and run later or captured into a variable, a Codex, Kilo Code or Copilot CLI shell behind a sandbox hop (parent branch), a plain pipe or substitution under a Cursor wrapper, Cursor's default PowerShell executor on Windows, Devin Desktop and the Devin CLI, VS Code Insiders, the Copilot harness in VS Code (not a listed parent) and agents that type into the integrated terminal are not covered | high |
| [`queries/kql/all-agent-shells-risky-command.kql`](queries/kql/all-agent-shells-risky-command.kql) | KQL over Defender XDR `DeviceProcessEvents`: a hunt over the programs started by an AI coding agent's shell (Cursor, Copilot CLI, Claude Code, Gemini CLI, Kilo Code, the legacy Windsurf terminal, Codex, Amazon Q), a shell of the Copilot harness under `copilot-runtime`, or a VS Code terminal (where GitHub Copilot under its Local harness, Cline's default and Roo Code's terminal mode type), with a `Source` column naming which, that name a credential source, or a download tool followed within 60 seconds by an interpreter in the same shell. It reads one level below the shell rule, so it also sees a Cursor download piped into `sh`, which splits into sibling children, and the native programs of Cursor's Windows PowerShell executor. It cannot tell an agent from a person in a terminal, and a program that replaces its shell (such as a lone command under the Copilot CLI's or Codex's shell) is not seen. As shipped the terminal source covers PowerShell terminals in VS Code on Windows; in-process PowerShell cmdlets start no process | query |
| [`rules/cross-platform/ai-agent-config-changed-by-command.yml`](rules/cross-platform/ai-agent-config-changed-by-command.yml) | A shell started by a coding agent (the same agents as `ai-agent-shell-risky-command`, kept equal by `--check`) changes an agent config file with `sed -i`, `tee`, `mv`, `cp`, a PowerShell write cmdlet or a redirect straight onto the path, or runs an `mcp add`; or an `mcp add` runs from a package folder under `node_modules`, seen by `CurrentDirectory`, because an install leaves no trace on the parent command line. Lines with `grep`, `rg` or read-only git commands are dropped. Does not see an agent's own Write or Edit tool. | medium |
| [`rules/cross-platform/ai-agent-config-new-file.yml`](rules/cross-platform/ai-agent-config-new-file.yml) | A new agent config file written straight to its final name by anything but git, or by an editor outside `.vscode` and `.cursor`: node, bun, python, a shell redirect, or an agent that writes in place. Does not see Claude Code's normal writes, which use a temp name and a rename, or an overwrite on Linux. Needs a Sysmon config that includes these paths. | medium |
| [`queries/kql/ai-agent-config-file-writes.kql`](queries/kql/ai-agent-config-file-writes.kql) | KQL over Defender XDR `DeviceFileEvents`: a hunt over every create, change or rename of these files and of hook and skill folders, with a `Writer` column (agent, editor, runtime, shell, git-or-package-tool, other) and runtimes and shells sorted first. The only pack file that can see Claude Code's file tools, or an agent editing an existing file. Every normal save is a row. Never run on real rows. | query |

Prerequisite: process-creation telemetry with full command lines (Sysmon Event 1,
Sysmon for Linux, auditd execve or EDR) from developer machines. The CLI-launch rule
has no parent condition: s1ngularity started the agent from node, the Amazon Q injection
(which never ran) would have used a shell, and CI does both. Scope it by host group: CI runners and agent sandboxes run
agents this way by design, so exclude them by host rather than by dropping a flag.

The shell rule keys on agent lineage, so it sees only agents that start their own
shells: the Claude Code wrapper string is a local observation of Claude Code 2.1.310
on Linux, and the extension-host branch matches any extension, not one agent. Tune
it by allowlisting exact commands per repository or host group, not by dropping a
branch.

The agent shells hunt reads one level below the shell rule: the programs an agent's
shell starts, not the shell's own command line. It keeps the children of the shells
the shell rule knows (by the same wrapper strings, now on the shell's command line as
seen from its child, or by the shell's parent as a bare file name), of a shell under
`copilot-runtime`, the Copilot harness in VS Code, and of a VS Code terminal shell
(grandparent `Code.exe`, shell-integration script on the shell's command line). It
leaves out the shells an extension starts straight from the extension host (Roo Code's
default mode), which only the shell rule covers. A
`Source` column names which, one per row. It pairs a download with an interpreter only
inside one shell, and most agents start a shell per command, so a download in one
command and a run in a later one do not pair. An unrelated interpreter run in the same
shell within the window pairs too, and so does a download piped into a parser such as
`python3 -m json.tool`; those are its main false positives. Add your Linux or macOS
editor process name to `Editors` once you have checked what your sensor records, and
add the file name to `RuntimeNames` if `chat.agentHost.copilot.runtimePath` renames
the runtime.

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
