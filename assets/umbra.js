/* UMBRASEC - shared interactivity
   Injects the ⌘K command palette, mobile menu, back-to-top button, and wires
   scroll-reveal, scrollspy, and code-copy buttons. Pages only need:
     <body data-base="">      (root pages)   or   data-base="../"  (subdirs)
     <script src="assets/umbra.js" defer></script>
*/
(function () {
  "use strict";

  const BASE = (document.body && document.body.dataset.base) || "";
  const url = (p) => (/^(https?:|mailto:|#)/.test(p) ? p : BASE + p);
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isMac = /Mac|iPhone|iPad|iPod/i.test(
    (navigator.userAgentData && navigator.userAgentData.platform) ||
    navigator.platform ||
    navigator.userAgent
  );

  // Show the visitor's own modifier key (⌘K on macOS/iOS, Ctrl K elsewhere)
  $$("[data-kbd]").forEach((el) => { el.textContent = isMac ? "⌘K" : "Ctrl K"; });

  /* ── Command palette data ─────────────────────────────────────── */
  // Keep entries grouped together and in GROUP_ORDER below. renderList emits a
  // group heading whenever the group changes as it walks the array, so a group
  // split across the array renders its heading more than once. The stable sort
  // after this array enforces it regardless of how new entries get appended.
  const COMMANDS = [
    { group: "Navigate", label: "Home", hint: "overview", icon: "fa-house", href: "./" },
    { group: "Navigate", label: "Approach", hint: "how this works", icon: "fa-compass", href: "./#approach", keywords: "method principles" },
    { group: "Navigate", label: "Research", hint: "all writeups", icon: "fa-flask", href: "research/", keywords: "articles posts" },
    { group: "Navigate", label: "Open Source", hint: "tools", icon: "fa-code-branch", href: "tools/", keywords: "tools github kev sigma blue team mapper red team mapper kev-watch kev watch umbra-blue skills detections claims ledger" },
    { group: "Navigate", label: "About", hint: "the project", icon: "fa-circle-info", href: "about" },
    { group: "Navigate", label: "Contact", hint: "get in touch", icon: "fa-envelope", href: "./#contact", keywords: "email" },
    { group: "Guide", label: "Security Guide", hint: "zero to defensible", icon: "fa-route", href: "guide/", keywords: "maturity essential eight iso 27001 nist csf roadmap journey foundation identity detection governance" },
    { group: "Guide", label: "Stage 1: Foundation", hint: "the cheap basics", icon: "fa-shield-halved", href: "guide/foundation", keywords: "foundation mfa backups patching admin asset inventory email phishing macros essential eight maturity level 1 basics" },
    { group: "Guide", label: "Stage 2: Identity & Access", hint: "the login is the perimeter", icon: "fa-id-badge", href: "guide/identity-and-access", keywords: "identity access sso single sign on conditional access mfa passkeys fido2 admin privileged joiner mover leaver password manager service accounts oauth consent least privilege" },
    { group: "Guide", label: "Stage 3: Detection & Response", hint: "someone has to watch the logs", icon: "fa-tower-observation", href: "guide/detection-and-response", keywords: "detection response edr mdr mssp soc logging audit log alerts incident response plan tabletop exercise breach notification notifiable data breach gdpr nis2 ransomware reporting build vs buy monitoring" },
    { group: "Guide", label: "Stage 4: Governance & Maturity", hint: "make the program provable", icon: "fa-landmark", href: "guide/governance-and-maturity", keywords: "governance maturity risk register policies supplier third party vendor risk board reporting metrics iso 27001 certification soc 2 smb1001 essential eight ml2 application control govern" },
    { group: "Tools", label: "sigma-pack", hint: "rules from the writeups", icon: "fa-filter", href: "tools/sigma-pack/", keywords: "sigma pack sigma-pack rules kql queries detections att&ck coverage" },
    { group: "Tools", label: "Blue Team Mapper", hint: "defender reference", icon: "fa-shield-halved", href: "https://umbrasec-labs.github.io/BlueTeamMapper/", external: true, keywords: "blue team mapper detection siem incident response threat hunting hardening soc defender reference soar" },
    { group: "Tools", label: "Red Team Mapper", hint: "attacker workflows, for defenders", icon: "fa-route", href: "https://umbrasec-labs.github.io/RedTeamMapper/", external: true, keywords: "red team mapper attacker workflows operation lifecycle flow chains adversary emulation purple team hunt coverage reference" },
    { group: "Tools", label: "umbra-blue", hint: "Claude Code skills", icon: "fa-puzzle-piece", href: "https://github.com/umbrasec-labs/umbra-blue", external: true, keywords: "umbra-blue claude code skills skill.md ai detection engineering incident response threat hunting hardening d3fend att&ck" },
    { group: "Tools", label: "Claims Ledger", hint: "detections", icon: "fa-scale-balanced", href: "https://github.com/umbrasec-labs/detections", external: true, keywords: "detections claims ledger sigma-pack ci tests synthetic events false positives blind spots attestation signed" },
    /* AUTO:articles START */
    { group: "Articles", label: "The Remote Support Appliance Was Open for Seven Weeks", hint: "BeyondTrust + privileged access", icon: "fa-headset", href: "research/beyondtrust-remote-support-armory-castle", keywords: "beyondtrust remote support bomgar cve-2026-102764 authentication bypass spoofing cwe-290 armory castle unc5221 warp panda mandiant google threat intelligence sawfly mangoapi webshell bareclaw socks5 websocket haproxy suid sudoers bt-secrets credential vault log deletion anti-forensics cisa kev msp third party risk privileged access espionage yara t1190 t1505.003 t1548.001 t1572 t1685.006" },
    { group: "Articles", label: "When the Allowlist Isn't a Boundary", hint: "Roo Code + AI agent auto-approve", icon: "fa-robot", href: "research/roo-code-auto-approve-bypass", keywords: "roo code cve-2026-110202 cve-2026-110203 cve-2026-110204 cve-2026-110205 cve-2026-110206 auto-approve command allowlist parsecommandline getcommanddecision parser differential indirect prompt injection ai coding agent vs code excessive agency confused deputy vulncheck archived unmaintained supply chain mitre atlas aml.t0051 t1698 t1059 t1554" },
    { group: "Articles", label: "php2shell and the Hallucinated Exploit", hint: "AI-generated PoCs vs the real PHP RCE", icon: "fa-ghost", href: "research/php2shell-hallucinated-exploits", keywords: "php2shell cve-2026-109618 cve-2026-109619 cve-2026-115560 php unauthenticated rce use after free cwe-416 session upload progress php_session_upload_progress session poisoning lfi orange tsai llm hallucinated exploit ai generated poc dunning kruger marcus hutchins malwaretech threat intelligence cisa kev mod_php php-fpm essential eight patch applications sigma t1190 segfault sigsegv" },
    { group: "Articles", label: "Sixteen Days From KEV to Exfiltration", hint: "Metabase + internal tooling", icon: "fa-chart-column", href: "research/mathspace-metabase-internal-tooling", keywords: "metabase cve-2026-72898 sql injection cwe-89 business intelligence bi internal tooling reporting database asset inventory asset discovery cisa kev kev-watch essential eight patch applications mathspace oaic notifiable data breach australian exfiltration sigma kql sentinel egress baseline t1190 t1213.006 t1567" },
    { group: "Articles", label: "Your MSP's RMM Is Your Attack Surface", hint: "N-central + third-party risk", icon: "fa-network-wired", href: "research/n-able-ncentral-msp-supply-chain", keywords: "n-able n-central rmm msp managed service provider supply chain third party risk cve-2026-18556 cve-2026-18577 authentication bypass cwe-288 cisa kev take control cloudflared cloudflare tunnel svchost masquerading persistence essential eight patch applications mfa supplier assurance australian sigma t1036.005 t1543.003 t1572" },
    { group: "Articles", label: "SafePay & Australian Real Estate", hint: "ransomware + Essential Eight", icon: "fa-building", href: "research/safepay-australian-smb", keywords: "safepay ransomware centralized non-raas australian real estate agency trust account essential eight asd acsc rdp vpn infostealer psexec winrm rclone filezilla exfiltration shadow copy backup deletion living off the land edge device fortinet citrix threat profile mitigation franchise sigma t1490 t1685 t1560.001 t1039 t1567.002 t1219.002 t1543.003 vssadmin wmic wbadmin bcdedit winrar 7-zip screenconnect anydesk teamviewer rmm remote access tool" },
    { group: "Articles", label: "How INC Ransom Hits Australian Organisations", hint: "RaaS + Essential Eight", icon: "fa-skull-crossbones", href: "research/inc-ransom-australian-smb", keywords: "inc ransom ransomware raas affiliate australian essential eight acsc asd ncsc nz cert tonga double extortion rclone megasync screenconnect rdp citrix netscaler fortinet phishing initial access broker living off the land net.exe defender lolbin threat profile mitigation sigma t1685 t1560.001 t1039 t1567.002 t1219.002 t1543.003 systemsettingsadminflows 7-zip anydesk teamviewer rmm remote access tool" },
    { group: "Articles", label: "Securing AI Agents", hint: "tool-calling LLMs", icon: "fa-robot", href: "research/securing-ai-agents", keywords: "ai agents agentic tool calling function calling excessive agency llm06 mcp model context protocol confused deputy indirect prompt injection lethal trifecta atlas autonomy human in the loop guardrails camel dual llm t1698 t1700" },
    { group: "Articles", label: "Detecting the LiteLLM Command Injection", hint: "CVE-2026-42271", icon: "fa-bug", href: "research/detecting-litellm-command-injection", keywords: "litellm cve-2026-42271 command injection rce mcp ai gateway proxy cisa kev starlette badhost cve-2026-48710 sigma t1190 berriai" },
    { group: "Articles", label: "OWASP LLM Top 10 for Defenders", hint: "prompt injection", icon: "fa-robot", href: "research/owasp-llm-top-10-for-defenders", keywords: "ai llm owasp prompt injection indirect atlas copilot echoleak agent rag canary t1698 t1699 t1700" },
    { group: "Articles", label: "Detecting OAuth Consent Phishing", hint: "T1528", icon: "fa-user-shield", href: "research/detecting-oauth-consent-phishing", keywords: "oauth consent phishing entra azure ad graph illicit grant token mfa m365 office 365 app credentials secret certificate service principal persistence t1098.001" },
    { group: "Articles", label: "Detecting Kerberoasting with Sigma", hint: "T1558.003", icon: "fa-shield-halved", href: "research/detecting-kerberoasting", keywords: "kerberos rc4 detection sigma active directory 4769" },
    /* AUTO:articles END */
    { group: "External", label: "GitHub", hint: "github.com/umbrasec-labs/umbrasec.dev", icon: "fa-github", brand: true, href: "https://github.com/umbrasec-labs/umbrasec.dev", external: true },
    { group: "External", label: "Email 0xdev1@umbrasec.dev", hint: "mail", icon: "fa-paper-plane", href: "mailto:0xdev1@umbrasec.dev", external: true },
  ];

  // Stable sort into GROUP_ORDER so each group heading renders exactly once,
  // whatever order entries were written or generated in. Array.prototype.sort
  // is stable in every browser that ships ES2019, so within-group order above
  // is preserved. Unknown groups sort to the end rather than being dropped.
  const GROUP_ORDER = ["Navigate", "Guide", "Tools", "Articles", "External"];
  const groupRank = (g) => {
    const i = GROUP_ORDER.indexOf(g);
    return i === -1 ? GROUP_ORDER.length : i;
  };
  COMMANDS.sort((a, b) => groupRank(a.group) - groupRank(b.group));

  /* ── Build command palette DOM ────────────────────────────────── */
  const overlay = document.createElement("div");
  overlay.className = "cmdk-overlay";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", "Search the site");
  overlay.innerHTML =
    '<div class="cmdk-panel">' +
      '<div class="cmdk-input-row">' +
        '<i class="fa-solid fa-magnifying-glass"></i>' +
        '<input class="cmdk-input" type="text" placeholder="Search pages, research, links…" aria-label="Command palette search" role="combobox" aria-expanded="true" aria-controls="cmdk-list" aria-autocomplete="list" autocomplete="off" spellcheck="false">' +
        '<span class="cmdk-hintkey">ESC</span>' +
      '</div>' +
      '<div class="cmdk-list" id="cmdk-list" role="listbox"></div>' +
    '</div>';
  document.body.appendChild(overlay);

  const input = $(".cmdk-input", overlay);
  const list = $(".cmdk-list", overlay);
  let activeIndex = 0;
  let filtered = [];
  let returnFocus = null;   // element to refocus when the palette closes

  function renderList(query) {
    const q = query.trim().toLowerCase();
    filtered = COMMANDS.filter((c) => {
      if (!q) return true;
      return (c.label + " " + (c.keywords || "") + " " + c.group).toLowerCase().includes(q);
    });
    activeIndex = 0;

    if (!filtered.length) {
      list.innerHTML = '<div class="cmdk-empty">No matches for “' + escapeHtml(query) + '”</div>';
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      return;
    }
    input.setAttribute("aria-expanded", "true");

    // Options sit in role="group" wrappers named by their heading, so the
    // listbox only holds groups and options.
    let html = "";
    let lastGroup = null;
    filtered.forEach((c, i) => {
      if (c.group !== lastGroup) {
        if (lastGroup !== null) html += "</div>";
        const gid = "cmdk-group-" + groupRank(c.group);
        html += '<div role="group" aria-labelledby="' + gid + '">' +
          '<div class="cmdk-group-label" id="' + gid + '">' + escapeHtml(c.group) + "</div>";
        lastGroup = c.group;
      }
      html +=
        '<div class="cmdk-item' + (i === 0 ? " active" : "") + '" role="option" id="cmdk-opt-' + i + '"' +
          ' aria-selected="' + (i === 0) + '" data-index="' + i + '">' +
          '<span class="ci-icon"><i class="' + (c.brand ? "fa-brands" : "fa-solid") + " " + c.icon + '"></i></span>' +
          '<span class="ci-label">' + escapeHtml(c.label) + "</span>" +
          '<span class="ci-hint">' + (c.external ? "↗ " : "") + escapeHtml(c.hint || "") + "</span>" +
        "</div>";
    });
    list.innerHTML = html + "</div>";
    input.setAttribute("aria-activedescendant", "cmdk-opt-0");

    $$(".cmdk-item", list).forEach((el) => {
      el.addEventListener("mouseenter", () => setActive(parseInt(el.dataset.index, 10)));
      el.addEventListener("click", () => go(filtered[parseInt(el.dataset.index, 10)]));
    });
  }

  function setActive(i) {
    activeIndex = i;
    $$(".cmdk-item", list).forEach((el) => {
      const on = parseInt(el.dataset.index, 10) === i;
      el.classList.toggle("active", on);
      el.setAttribute("aria-selected", on);
    });
    const el = list.querySelector('.cmdk-item[data-index="' + i + '"]');
    if (el) {
      input.setAttribute("aria-activedescendant", el.id);
      el.scrollIntoView({ block: "nearest" });
    }
  }

  function go(cmd) {
    if (!cmd) return;
    closePalette();
    if (cmd.external) {
      window.open(cmd.href, cmd.href.startsWith("mailto:") ? "_self" : "_blank", "noopener");
    } else {
      window.location.href = url(cmd.href);
    }
  }

  function openPalette() {
    if (overlay.classList.contains("open")) return;
    const prev = document.activeElement;
    returnFocus = prev && prev !== document.body ? prev : null;
    overlay.classList.add("open");
    input.value = "";
    renderList("");
    setTimeout(() => input.focus(), 30);
  }
  function closePalette() {
    overlay.classList.remove("open");
    // hand focus back to whatever opened the palette (button, link, field)
    const back = returnFocus;
    returnFocus = null;
    if (back && back.isConnected) back.focus({ preventScroll: true });
  }
  function togglePalette() {
    overlay.classList.contains("open") ? closePalette() : openPalette();
  }

  input.addEventListener("input", () => renderList(input.value));
  overlay.addEventListener("mousedown", (e) => {
    // preventDefault keeps the browser from moving focus to <body> after
    // closePalette() has handed it back
    if (e.target === overlay) { e.preventDefault(); closePalette(); }
  });

  document.addEventListener("keydown", (e) => {
    const open = overlay.classList.contains("open");
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      togglePalette();
      return;
    }
    if (!open) return;
    if (e.key === "Escape") { e.preventDefault(); closePalette(); }
    // the input is the dialog's only focusable element, so Tab and
    // Shift+Tab stay on it instead of leaving the aria-modal dialog
    else if (e.key === "Tab") { e.preventDefault(); input.focus(); }
    else if (e.key === "ArrowDown") { e.preventDefault(); if (filtered.length) setActive((activeIndex + 1) % filtered.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); if (filtered.length) setActive((activeIndex - 1 + filtered.length) % filtered.length); }
    else if (e.key === "Enter") { e.preventDefault(); go(filtered[activeIndex]); }
  });

  // any element with data-cmdk opens the palette (e.g. the ⌘K nav button)
  $$("[data-cmdk]").forEach((el) => el.addEventListener("click", openPalette));

  /* ── Mobile menu (built from the desktop nav links) ───────────── */
  (function buildMobileMenu() {
    const nav = $("nav");
    if (!nav) return;
    const desktop = nav.querySelector(".md\\:flex");
    const links = desktop ? $$("a", desktop) : [];
    if (!links.length) return;

    const btn = document.createElement("button");
    btn.className = "menu-btn md:hidden";
    btn.setAttribute("aria-label", "Toggle menu");
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-controls", "mobile-menu");
    btn.innerHTML = '<i class="fa-solid fa-bars text-lg"></i>';

    // place the button at the far right of the nav bar
    const bar = nav.querySelector(".flex.items-center.justify-between");
    if (bar) {
      btn.classList.add("ml-1");
      bar.appendChild(btn);
    }

    const panel = document.createElement("div");
    panel.id = "mobile-menu";
    panel.className = "mobile-menu md:hidden px-8";
    links.forEach((src) => {
      const a = document.createElement("a");
      a.href = src.getAttribute("href");
      a.textContent = src.textContent.trim();
      panel.appendChild(a);
    });
    nav.appendChild(panel);

    btn.addEventListener("click", () => {
      const open = panel.classList.toggle("open");
      btn.setAttribute("aria-expanded", String(open));
      btn.innerHTML = open
        ? '<i class="fa-solid fa-xmark text-lg"></i>'
        : '<i class="fa-solid fa-bars text-lg"></i>';
    });
    $$("a", panel).forEach((a) =>
      a.addEventListener("click", () => {
        panel.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
        btn.innerHTML = '<i class="fa-solid fa-bars text-lg"></i>';
      })
    );
  })();

  /* ── Scroll-reveal ────────────────────────────────────────────── */
  (function reveal() {
    const targets = $$("section, .reveal");
    if (reduceMotion || !("IntersectionObserver" in window)) {
      targets.forEach((t) => t.classList.add("is-visible"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            en.target.classList.add("is-visible");
            io.unobserve(en.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -8% 0px" }
    );
    targets.forEach((t) => {
      // already on screen at load → show immediately, no hide-then-reveal flicker
      if (t.getBoundingClientRect().top < window.innerHeight * 0.9) {
        t.classList.add("is-visible");
      } else {
        t.classList.add("reveal");
        io.observe(t);
      }
    });
  })();

  /* ── Scrollspy (active nav link) ──────────────────────────────── */
  (function scrollspy() {
    const navLinks = $$("nav a.nav-link").filter((a) => (a.getAttribute("href") || "").includes("#"));
    const map = new Map();
    navLinks.forEach((a) => {
      const id = (a.getAttribute("href") || "").split("#")[1];
      const sec = id && document.getElementById(id);
      if (sec) map.set(sec, a);
    });
    if (!map.size || !("IntersectionObserver" in window)) return;
    // Activate when a section crosses a band in the upper-middle of the
    // viewport - a visible-ratio threshold never fires on sections taller
    // than the viewport.
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          const a = map.get(en.target);
          if (!a) return;
          if (en.isIntersecting) {
            navLinks.forEach((l) => l.classList.remove("active"));
            a.classList.add("active");
          }
        });
      },
      { rootMargin: "-35% 0px -55% 0px", threshold: 0 }
    );
    map.forEach((_, sec) => io.observe(sec));
  })();

  /* ── Code copy buttons ────────────────────────────────────────── */
  let codeCount = 0;
  $$(".prose pre").forEach((pre) => {
    const wrap = document.createElement("div");
    wrap.className = "code-wrap";
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);

    // A block that scrolls sideways must be reachable by keyboard (Safari
    // does not focus scroll containers on its own) and needs a unique name.
    if (pre.scrollWidth > pre.clientWidth) {
      pre.tabIndex = 0;
      pre.setAttribute("role", "region");
      pre.setAttribute("aria-label", "Code sample " + ++codeCount);
    }

    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = "Copy";
    wrap.appendChild(btn);

    btn.addEventListener("click", () => {
      const text = pre.innerText;
      const done = () => {
        btn.textContent = "Copied";
        btn.classList.add("copied");
        setTimeout(() => {
          btn.textContent = "Copy";
          btn.classList.remove("copied");
        }, 1600);
      };
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(done).catch(fallbackCopy);
      } else {
        fallbackCopy();
      }
      function fallbackCopy() {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); done(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
  });

  /* ── Copy-to-clipboard helpers ─────────────────────────── */
  function legacyCopy(text) {
    return new Promise((resolve, reject) => {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.top = "0";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      let ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      ok ? resolve() : reject(new Error("copy unavailable"));
    });
  }
  // Try the async Clipboard API; if it rejects (no focus / denied / insecure
  // context) fall back to execCommand, and reject only if both fail - so a
  // failed copy never silently leaves stale clipboard content behind.
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(() => legacyCopy(text));
    }
    return legacyCopy(text);
  }

  $$("[data-copy]").forEach((el) => {
    el.addEventListener("click", () => {
      const value = el.getAttribute("data-copy");
      copyText(value).then(() => {
        el.classList.add("copied");
        const addr = el.querySelector(".dc-addr");
        const prev = addr ? addr.textContent : null;
        if (addr) addr.textContent = "Copied ✓";
        setTimeout(() => {
          el.classList.remove("copied");
          if (addr && prev !== null) addr.textContent = prev;
        }, 1500);
      }).catch(() => { window.prompt("Copy this:", value); });
    });
  });

  /* ── Wide tables: keyboard-scrollable like code blocks ────────── */
  $$(".table-wrap").forEach((wrap, i) => {
    if (wrap.scrollWidth <= wrap.clientWidth) return;
    const cap = wrap.querySelector("caption");
    wrap.tabIndex = 0;
    wrap.setAttribute("role", "region");
    wrap.setAttribute("aria-label", cap ? cap.textContent.trim() : "Table " + (i + 1));
  });

  /* ── Research category filter (research index only) ───────────── */
  (function researchFilter() {
    const bar = $("[data-research-filter]");
    const grid = $("[data-research-grid]");
    if (!bar || !grid) return;
    const cards = $$("[data-cat]", grid);
    const empty = $("[data-research-empty]");

    bar.addEventListener("click", (e) => {
      const chip = e.target.closest(".filter-chip");
      if (!chip) return;
      const filter = chip.dataset.filter;
      $$(".filter-chip", bar).forEach((c) => {
        c.classList.toggle("active", c === chip);
        c.setAttribute("aria-pressed", String(c === chip));
      });

      let shown = 0;
      cards.forEach((card) => {
        const match = filter === "all" || card.dataset.cat === filter;
        card.classList.toggle("hidden", !match);
        if (match) shown++;
      });
      if (empty) empty.classList.toggle("hidden", shown > 0);
    });
  })();

  /* ── Decode / scramble text ───────────────────────────────────── */
  (function scrambleText() {
    if (reduceMotion || !("IntersectionObserver" in window)) return;
    const GLYPHS = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789!<>-_\\/[]{}=+*^?#%&";
    const els = $$("[data-scramble], .section-label");
    if (!els.length) return;

    function run(el) {
      if (el.dataset.scrambled) return;
      el.dataset.scrambled = "1";
      const finalText = el.textContent;
      const queue = finalText.split("").map((ch) => {
        if (ch === " ") return { ch, space: true };
        const start = Math.floor(Math.random() * 12);
        return { ch, start, end: start + 12 + Math.floor(Math.random() * 20), rnd: null };
      });
      let frame = 0;
      (function tick() {
        let out = "", done = 0;
        for (const q of queue) {
          if (q.space) { out += " "; done++; continue; }
          if (frame >= q.end) { out += escapeHtml(q.ch); done++; }
          else if (frame >= q.start) {
            if (!q.rnd || Math.random() < 0.3) q.rnd = GLYPHS[(Math.random() * GLYPHS.length) | 0];
            out += '<span class="scramble-rnd">' + escapeHtml(q.rnd) + "</span>";
          }
        }
        // screen readers get the final text, never the random glyphs
        el.innerHTML = '<span class="visually-hidden">' + escapeHtml(finalText) + "</span>" +
          '<span aria-hidden="true">' + out + "</span>";
        frame++;
        if (done < queue.length) requestAnimationFrame(tick);
        else el.textContent = finalText;
      })();
    }

    const io = new IntersectionObserver(
      (entries) => entries.forEach((en) => {
        if (en.isIntersecting) { run(en.target); io.unobserve(en.target); }
      }),
      { threshold: 0.4 }
    );
    els.forEach((el) => io.observe(el));
  })();

  /* ── Hero network constellation (mouse-reactive) ──────────────── */
  (function heroNetwork() {
    if (reduceMotion) return;
    const hero = $(".hero");
    if (!hero || !("requestAnimationFrame" in window)) return;

    const canvas = document.createElement("canvas");
    canvas.className = "hero-canvas";
    canvas.setAttribute("aria-hidden", "true");
    hero.insertBefore(canvas, hero.firstChild);
    const ctx = canvas.getContext("2d");

    const COUNT = 42, LINK = 132, MOUSE_R = 170;
    let w, h, dpr, nodes = [], raf = null, running = true;
    const mouse = { x: -9999, y: -9999 };

    function size() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = hero.clientWidth; h = hero.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      canvas.style.width = w + "px"; canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function seed() {
      nodes = [];
      for (let i = 0; i < COUNT; i++) {
        nodes.push({
          x: Math.random() * w, y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
        });
      }
    }
    function step() {
      ctx.clearRect(0, 0, w, h);
      for (const n of nodes) {
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;
      }
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          const d = Math.hypot(a.x - b.x, a.y - b.y);
          if (d < LINK) {
            ctx.strokeStyle = "rgba(242,86,35," + (1 - d / LINK) * 0.22 + ")";
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          }
        }
      }
      for (const n of nodes) {
        const dm = Math.hypot(n.x - mouse.x, n.y - mouse.y);
        const near = dm < MOUSE_R;
        ctx.beginPath();
        ctx.arc(n.x, n.y, near ? 2.4 : 1.5, 0, Math.PI * 2);
        ctx.fillStyle = near
          ? "rgba(245,110,15," + (0.5 + (1 - dm / MOUSE_R) * 0.5) + ")"
          : "rgba(242,86,35,0.45)";
        ctx.fill();
        if (near) {
          ctx.strokeStyle = "rgba(245,110,15," + (1 - dm / MOUSE_R) * 0.5 + ")";
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
        }
      }
      if (running) raf = requestAnimationFrame(step);
    }

    size(); seed(); step();
    let rt;
    window.addEventListener("resize", () => {
      clearTimeout(rt);
      rt = setTimeout(() => { size(); seed(); }, 150);
    });
    hero.addEventListener("mousemove", (e) => {
      const r = hero.getBoundingClientRect();
      mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
    });
    hero.addEventListener("mouseleave", () => { mouse.x = mouse.y = -9999; });

    if ("IntersectionObserver" in window) {
      new IntersectionObserver((es) => es.forEach((en) => {
        running = en.isIntersecting;
        if (running && raf === null) { raf = requestAnimationFrame(step); }
        if (!running && raf !== null) { cancelAnimationFrame(raf); raf = null; }
      }), { threshold: 0 }).observe(hero);
    }
  })();

  /* ── Article table of contents + scrollspy ────────────────────── */
  (function tableOfContents() {
    const rail = $("[data-toc]");
    if (!rail) return;
    const headings = $$("article .prose h2");
    if (!headings.length) return;

    const slugify = (t) =>
      t.toLowerCase().replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "-").slice(0, 60) || "section";
    const used = new Set();

    let html = '<div class="toc"><div class="toc-title">On this page</div><nav aria-label="On this page">';
    const entries = [];
    headings.forEach((h) => {
      let id = h.id || slugify(h.textContent);
      while (used.has(id)) id += "-1";
      used.add(id);
      h.id = id;
      html += '<a href="#' + escapeHtml(id) + '">' + escapeHtml(h.textContent) + "</a>";
      entries.push({ el: h });
    });
    html += "</nav></div>";
    rail.innerHTML = html;

    const links = $$("a", rail);
    links.forEach((a, i) => { entries[i].link = a; });

    if (!("IntersectionObserver" in window)) return;
    const linkFor = new Map(entries.map((e) => [e.el, e.link]));
    const io = new IntersectionObserver(
      (obs) => obs.forEach((en) => {
        if (en.isIntersecting) {
          links.forEach((l) => l.classList.remove("active"));
          const link = linkFor.get(en.target);
          if (link) link.classList.add("active");
        }
      }),
      { rootMargin: "-80px 0px -70% 0px", threshold: 0 }
    );
    entries.forEach((e) => io.observe(e.el));
  })();

  /* ── Reading progress bar (pages with data-reading) ───────────── */
  (function readingProgress() {
    if (!document.body.hasAttribute("data-reading")) return;
    const bar = document.createElement("div");
    bar.className = "read-progress";
    bar.setAttribute("aria-hidden", "true");
    document.body.appendChild(bar);
    const doc = document.documentElement;
    let ticking = false;
    function update() {
      const max = doc.scrollHeight - doc.clientHeight;
      bar.style.width = (max > 0 ? (doc.scrollTop / max) * 100 : 0) + "%";
    }
    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => { update(); ticking = false; });
    }, { passive: true });
    window.addEventListener("resize", update);
    update();
  })();

  /* ── CISA KEV live ticker (homepage) ──────────────────────────── */
  (function kevTicker() {
    const strip = $("[data-kev-ticker]");
    if (!strip) return;
    const track = $("[data-kev-track]", strip);
    if (!track) return;

    // Turn the CSS marquee into a grab-and-drag strip: a rAF loop drives the
    // same left-drift, and pointer drags pull it back and forth, wrapping
    // seamlessly. On release the auto-scroll resumes. Reduced-motion users keep
    // the native overflow-x scroll fallback and never reach this.
    function makeKevDraggable(strip, track) {
      const viewport = $(".kev-viewport", strip);
      if (!viewport) return;

      track.classList.add("is-interactive");
      viewport.classList.add("is-grabbable");

      // Links and icons are natively draggable; without this the browser starts
      // a link drag on mouse-move, which fires pointercancel and kills our drag.
      viewport.addEventListener("dragstart", (e) => e.preventDefault());

      let half = track.scrollWidth / 2;      // width of one (un-duplicated) row
      let speed = half / 42000;              // px/ms - matches the old 42s / -50% drift
      // The drift stops while any of these holds: pointer over the strip, a
      // link in it has keyboard focus, or the pause button is on.
      let offset = 0, hovered = false, focused = false, userPaused = false, dragging = false, moved = false;
      let pointerId = null, startX = 0, startOffset = 0, last = 0;

      const wrap = (x) => { let m = half > 0 ? x % half : 0; if (m > 0) m -= half; return m; };
      const apply = () => { track.style.transform = "translateX(" + offset + "px)"; };

      function frame(now) {
        const dt = last ? now - last : 0; last = now;
        if (!hovered && !focused && !userPaused && !dragging && half > 0) { offset = wrap(offset - speed * dt); apply(); }
        requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);

      // Hovering pauses the drift, matching the old CSS behaviour.
      viewport.addEventListener("mouseenter", () => { hovered = true; });
      viewport.addEventListener("mouseleave", () => { if (!dragging) hovered = false; });

      // Keyboard focus pauses the drift and slides the focused link fully into
      // view (inset past the 40px edge fade). Only the first run is focusable,
      // so the offset is not wrapped here. Mouse clicks don't count, so a drag
      // that starts on a link doesn't jump.
      const EDGE = 40;
      viewport.addEventListener("focusin", (e) => {
        const a = e.target.closest ? e.target.closest(".kev-item") : null;
        if (!a || !a.matches(":focus-visible")) return;
        focused = true;
        viewport.scrollLeft = 0;              // undo the browser's own scroll-into-view
        const r = a.getBoundingClientRect(), v = viewport.getBoundingClientRect();
        const rel = r.left - v.left;
        // a link wider than the strip (phones) is aligned by its start
        if (rel < EDGE || r.width > v.width - 2 * EDGE) offset += EDGE - rel;
        else if (rel + r.width > v.width - EDGE) offset -= rel + r.width - (v.width - EDGE);
        offset = Math.min(0, offset);
        apply();
      });
      viewport.addEventListener("focusout", (e) => {
        if (!viewport.contains(e.relatedTarget)) focused = false;
      });
      viewport.addEventListener("scroll", () => { viewport.scrollLeft = 0; });

      // Visible pause/play control (WCAG 2.2.2). It sits before the strip so it
      // is the first tab stop in the ticker.
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "kev-toggle";
      const setToggle = () => {
        const label = userPaused ? "Play the KEV ticker" : "Pause the KEV ticker";
        toggle.setAttribute("aria-label", label);
        toggle.title = label;
        toggle.innerHTML = '<i class="fa-solid ' + (userPaused ? "fa-play" : "fa-pause") + '" aria-hidden="true"></i>';
      };
      setToggle();
      toggle.addEventListener("click", () => { userPaused = !userPaused; setToggle(); });
      viewport.parentNode.insertBefore(toggle, viewport);

      viewport.addEventListener("pointerdown", (e) => {
        if (e.pointerType === "mouse" && e.button !== 0) return;
        dragging = true; moved = false;
        startX = e.clientX; startOffset = offset; pointerId = e.pointerId;
        half = track.scrollWidth / 2;        // re-measure in case fonts shifted widths
        try { viewport.setPointerCapture(pointerId); } catch (_) {}
        viewport.classList.add("is-grabbing");
      });

      viewport.addEventListener("pointermove", (e) => {
        if (!dragging) return;
        const dx = e.clientX - startX;
        if (Math.abs(dx) > 3) moved = true;
        offset = wrap(startOffset + dx);
        apply();
      });

      function endDrag() {
        if (!dragging) return;
        dragging = false;
        viewport.classList.remove("is-grabbing");
        if (pointerId !== null) { try { viewport.releasePointerCapture(pointerId); } catch (_) {} pointerId = null; }
        hovered = viewport.matches(":hover");  // resume once the pointer leaves
      }
      viewport.addEventListener("pointerup", endDrag);
      viewport.addEventListener("pointercancel", endDrag);

      // A drag ends in a click on the underlying link - swallow it so we don't
      // navigate to CVE.org after the user was only scrubbing the strip.
      track.addEventListener("click", (e) => {
        if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; }
      }, true);

      window.addEventListener("resize", () => {
        half = track.scrollWidth / 2; speed = half / 42000;
      }, { passive: true });
    }

    // Live first: /api/kev is a Pages Function (functions/api/kev.js) that
    // fetches and trims CISA's catalog on demand and edge-caches it, so the
    // strip refreshes itself. If that fails (function error, local preview
    // without wrangler), fall back to the committed snapshot that
    // tools/local-sync/sync-kev.py maintains.
    const load = (src) => fetch(src)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("http " + r.status))))
      // an empty payload counts as a failure too, so the snapshot gets its turn
      .then((d) => (((d && d.vulnerabilities) || []).length ? d : Promise.reject(new Error("empty"))));
    load(url("api/kev"))
      .catch(() => load(url("assets/kev-latest.json")))
      .then((data) => {
        const items = (data.vulnerabilities || []).slice(0, 10);
        if (!items.length) return; // nothing to show → stay hidden, never fake it

        // dup: the copy that makes the loop seamless - hidden from screen
        // readers and the tab order so each entry is announced once
        const row = (dup) => items.map((v) => {
          const ransom = v.knownRansomwareCampaignUse === "Known"
            ? ' <i class="fa-solid fa-skull-crossbones kev-ransom" title="Known ransomware campaign use"></i>'
            : "";
          const cve = v.cveID || "";
          const href = "https://www.cve.org/CVERecord?id=" + encodeURIComponent(cve);
          return '<a class="kev-item" href="' + href + '" target="_blank" rel="noopener" draggable="false"' +
              (dup ? ' aria-hidden="true" tabindex="-1"' : "") +
              ' title="View ' + escapeHtml(cve) + ' on CVE.org">' +
              '<span class="kev-cve">' + escapeHtml(cve) + "</span>" +
              '<span class="kev-prod">' + escapeHtml(((v.vendorProject || "") + " " + (v.product || "")).trim()) + "</span>" +
              ransom +
              '<span class="kev-date">' + escapeHtml(v.dateAdded || "") + "</span>" +
            "</a>";
        }).join("");

        // duplicate run for a seamless loop - skip when the scroll animation
        // is disabled, so reduced-motion users don't see every item twice
        track.innerHTML = reduceMotion ? row(false) : row(false) + row(true);
        const tag = $(".kev-tag", strip);
        if (tag) {
          tag.title = "Latest CISA KEV additions · catalog " + (data.catalogVersion || "?") +
            (data.mode === "live" ? " · live" : " · snapshot " + (data.synced || ""));
        }
        strip.classList.remove("hidden");

        // Enable drag-to-scroll once the strip is laid out (reduced-motion keeps
        // the native scroll fallback, so skip the rAF marquee there).
        if (!reduceMotion) makeKevDraggable(strip, track);
      })
      .catch(() => { /* leave the strip hidden - show real data or nothing */ });
  })();

  /* ── Back to top ──────────────────────────────────────────────── */
  (function backToTop() {
    const btn = document.createElement("button");
    btn.className = "to-top";
    btn.setAttribute("aria-label", "Back to top");
    btn.innerHTML = '<i class="fa-solid fa-arrow-up"></i>';
    document.body.appendChild(btn);
    btn.addEventListener("click", () =>
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" })
    );
    let ticking = false;
    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        btn.classList.toggle("show", window.scrollY > 600);
        ticking = false;
      });
    });
  })();

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }
})();
