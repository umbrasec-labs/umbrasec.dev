"""
hero_reel.py - the homepage trace-to-rule reel, generated from the sigma-pack
and the Claims Ledger.

One example per pack file: the ATT&CK technique from the README coverage
table, one synthetic event from the file's claims in
../detections/claims/<name>.yml, and the rule (or query) lines that catch it,
with the matching values highlighted on both sides. Every line comes from the
files themselves, so a rule or claim edit regenerates the reel instead of
leaving the hero quoting lines the pack no longer has.

tools/site-build/hero-reel.json sets the order (every pack file once, the
first one is what a visitor without JavaScript sees) and, per file, optional
overrides where the defaults pick badly:

  technique   ATT&CK id from the file's README row (default: the first one)
  tactic      one of the row's tactics (default: the only one, or the one in
              the same position as the technique; an error when that is
              ambiguous)
  claim       claim id (default: the first catches/* claim with expect: match)
  event_keys  event fields to show, in order (default: _synthetic, then the
              fields the rule names, in claim order)
  rule_lines  rule lines to show, stripped of indentation and comments, in
              file order; "..." marks left-out lines (default: the whole
              detection or correlation block, or the query, cut down to the
              highlighted lines and their parents when it is too long)
  highlight   event fields whose matches are highlighted (default: every
              field the shown rule lines match, except EventID and Status)
  event       which event of the claim to show, by index (default: 0)

Called by build_indexes.py only when the detections checkout sits next to
this repo (the workspace); it needs PyYAML for the claims files.
"""

import hashlib
import html
import json
import re
import sys

KQL_CAP = 9        # query lines shown by default, from the top
RULE_CAP = 12      # rule lines per example, "..." lines included
EVENT_CAP = 6      # event lines per example, _synthetic included
VALUE_CAP = 58     # characters of one event value before it is cut
QUIET = {"EventID", "Status"}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
KEY_RE = re.compile(r"""^(- )?([A-Za-z_][\w.|-]*):(?: (.*))?$""")
ITEM_RE = re.compile(r"^- (.+)$")
QUOTED_RE = re.compile(r"""'(?:[^']|'')*'|"(?:[^"\\]|\\.)*\"""")


def fail(msg):
    sys.exit(f"error: hero reel: {msg}")


def he(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---- reading the sources --------------------------------------------------------

def strip_comment(line, marker):
    """Drop a trailing comment that starts outside quotes."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif line.startswith(marker, i) and (i == 0 or line[i - 1] in " \t"):
            return line[:i].rstrip()
    return line.rstrip()


def clean_lines(text, marker):
    """(indent, text) for each line, comments and blank lines dropped."""
    out = []
    for raw in text.splitlines():
        ln = strip_comment(raw, marker)
        if ln.strip():
            out.append((len(ln) - len(ln.lstrip(" ")), ln.strip()))
    return out


def yaml_block(text, key):
    """The children of the first top-level `key:` in a YAML file, dedented."""
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip() == f"{key}:")
    except StopIteration:
        return None
    body = []
    for ln in lines[start + 1:]:
        if ln.strip() and not ln.startswith((" ", "#")):
            break
        body.append(ln)
    block = clean_lines("\n".join(body), "#")
    if not block:
        return None
    base = block[0][0]
    return [(ind - base, t) for ind, t in block]


def kql_lines(text):
    """The query from its first non-comment line (the table)."""
    return clean_lines(text, "//")


def parse_attack(row):
    """[(id, name)] from a README coverage row."""
    out = []
    for part in re.split(r";\s*(?=\[)", row["attack"]):
        m = MD_LINK_RE.search(part)
        if m:
            out.append((m.group(1), html.unescape(part[m.end():].strip())))
    return out


def load_claim(claims_path, claim_id, event_index=0):
    try:
        import yaml  # only the workspace build needs it
    except ImportError:
        fail("PyYAML is needed to read ../detections/claims (pip install pyyaml)")
    data = yaml.safe_load(claims_path.read_text(encoding="utf-8"))
    claims = data.get("claims") or []
    if claim_id:
        hit = [c for c in claims if c.get("id") == claim_id]
        if not hit:
            fail(f"{claims_path.name}: no claim {claim_id}")
        claim = hit[0]
    else:
        hit = [c for c in claims if str(c.get("id", "")).startswith("catches/") and c.get("expect") == "match"]
        if not hit:
            fail(f"{claims_path.name}: no catches/* claim with expect: match")
        claim = hit[0]
    if claim.get("expect") != "match":
        fail(f"{claims_path.name}: claim {claim['id']} does not expect a match")
    defaults = dict(data.get("event_defaults") or {})
    more = ""
    if "generate" in claim:
        g = claim["generate"]
        event = {k: (v.format(i=1) if isinstance(v, str) else v) for k, v in g["template"].items()}
        more = f"... {g['count']} events, {g['step_seconds']}s apart"
    else:
        events = claim.get("events") or []
        if not events:
            fail(f"{claims_path.name}: claim {claim['id']} has no events")
        if not -len(events) <= event_index < len(events):
            fail(f"{claims_path.name}: claim {claim['id']} has no event {event_index}")
        event = events[event_index]
        n = len(events) - 1
        if n:
            s = "s" if n > 1 else ""
            if data.get("engine") == "kusto":
                more = f"... +{n} more row{s} in the table"
            elif claim.get("mode", "each") == "sequence":
                more = f"... +{n} more event{s}, matched together"
            else:
                more = f"... +{n} more event{s}, each caught alone"
    merged = {**defaults, **event}
    merged.pop("_note", None)
    return claim["id"], merged, more, data.get("engine", "sigma")


# ---- matching ---------------------------------------------------------------------

def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        inner = v[1:-1]
        return inner.replace("''", "'") if v[0] == "'" else inner.replace('\\"', '"').replace("\\\\", "\\")
    return v


def value_text(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    return str(v)


def sigma_literals(lines):
    """(line index, field, modifiers, literal, span) for each value a Sigma block compares."""
    out, parents = [], []  # parents: (indent, field, mods)
    for i, (ind, t) in enumerate(lines):
        while parents and parents[-1][0] >= ind:
            parents.pop()
        m = KEY_RE.match(t)
        if m:
            field, _, mods = m.group(2).partition("|")
            parents.append((ind + (2 if m.group(1) else 0), field, mods))
            if m.group(3):
                val = m.group(3)
                out.append((i, field, mods, val, (t.rindex(val), len(t))))
            continue
        m = ITEM_RE.match(t)
        if m and parents:
            _, field, mods = parents[-1]
            out.append((i, field, mods, m.group(1), (2, len(t))))
    return out


def sigma_hit(mods, lit, value):
    """Where lit matches value under the Sigma modifiers, as a (start, end) in value."""
    if "re" in mods.split("|") or "cidr" in mods.split("|"):
        return None
    lit = unquote(lit).strip("*").replace("\\\\", "\\")
    if not lit:
        return None
    v, lo = value, lit.lower()
    pos = v.lower().find(lo)
    if pos < 0:
        return None
    if "endswith" in mods and not v.lower().endswith(lo):
        return None
    if "startswith" in mods and not v.lower().startswith(lo):
        return None
    if not any(m in mods for m in ("contains", "endswith", "startswith")) and v.lower() != lo:
        return None
    return pos, pos + len(lit)


def kql_hits(lines, event):
    """(line index, span, field, value span) for each string literal of the query found in an event value."""
    out = []
    for i, (_, t) in enumerate(lines):
        for m in QUOTED_RE.finditer(t):
            lit = unquote(m.group(0))
            if len(lit) < 3:
                continue
            for field, v in event.items():
                pos = value_text(v).lower().find(lit.lower())
                if pos >= 0 and field != "_synthetic":
                    out.append((i, m.span(), field, (pos, pos + len(lit))))
                    break
    return out


# ---- choosing what to show ----------------------------------------------------------

def pick_lines(lines, keep, cap):
    """Indices to show: all if they fit, else the kept ones and their parents."""
    if len(lines) <= cap:
        return list(range(len(lines)))
    if not keep:
        return list(range(cap - 1))  # with_gaps adds the closing "..."
    want = set()
    for i in keep:
        want.add(i)
        ind = lines[i][0]
        for j in range(i - 1, -1, -1):
            if lines[j][0] < ind:
                want.add(j)
                ind = lines[j][0]
                if ind == 0:
                    break
    return sorted(want)


def with_gaps(lines, idx):
    """[(indent, text, dim)] for the chosen indices, a "..." line per gap."""
    out, prev = [], -1
    for i in idx:
        if i != prev + 1:
            out.append((lines[prev + 1][0], "...", True, None))
        out.append((lines[i][0], lines[i][1], False, i))
        prev = i
    if idx and idx[-1] != len(lines) - 1:
        out.append((lines[idx[-1] + 1][0], "...", True, None))
    return out


def manual_lines(lines, wanted, name):
    """The rule_lines override, located in order; returns indices with None for gaps."""
    out, pos = [], 0
    for w in wanted:
        if w == "...":
            out.append(None)
            continue
        hit = next((j for j in range(pos, len(lines)) if lines[j][1] == w), None)
        if hit is None:
            fail(f"{name}: rule line '{w}' not found (in order)")
        if out and out[-1] is not None and hit != out[-1] + 1:
            fail(f"{name}: rule line '{w}' does not follow the line before it; mark the gap with ...")
        out.append(hit)
        pos = hit + 1
    real = [i for i in out if i is not None]
    if real and real[0] != 0 and out[0] is not None:
        fail(f"{name}: rule_lines skip the lines before '{wanted[0]}'; start with ...")
    if real and real[-1] != len(lines) - 1 and out[-1] is not None:
        fail(f"{name}: rule_lines stop before the end of the block; end with ...")
    rows = []
    for k, i in enumerate(out):
        if i is None:
            nxt = next((x for x in out[k + 1:] if x is not None), None)
            prv = next((x for x in reversed(out[:k]) if x is not None), None)
            ref = (prv + 1) if prv is not None else nxt
            rows.append((lines[min(ref, len(lines) - 1)][0], "...", True, None))
        else:
            rows.append((lines[i][0], lines[i][1], False, i))
    return rows


# ---- rendering ------------------------------------------------------------------------

def fmt_value(v):
    """(display text, class) for an event value, quoted the way YAML would need it."""
    if isinstance(v, bool):
        return ("true" if v else "false"), "n"
    if v is None:
        return "null", "n"
    if isinstance(v, (int, float)):
        return str(v), "n"
    s = str(v)
    plain = re.fullmatch(r"[A-Za-z_./\\$@~][\w./\\$@~:-]*", s) and not s.endswith(":")
    if plain and not re.fullmatch(r"(?i)true|false|null|yes|no|0x[0-9a-f]+|[0-9.]+", s):
        return s, "s"
    # single quotes keep backslashes literal, as YAML reads them
    if ('"' in s or "\\" in s) and "'" not in s:
        return "'" + s + "'", "s"
    return '"' + s + '"', "s"


def cut(text, span):
    """Shorten text to VALUE_CAP characters around span (a highlight), "..." where cut."""
    """Returns the new text, the (start, end) of text it still shows, and the
    shift that maps a position in that range to its place in the new text."""
    if len(text) <= VALUE_CAP:
        return text, (0, len(text)), 0
    if span is None or span[1] <= VALUE_CAP - 3:
        return text[:VALUE_CAP - 3] + "...", (0, VALUE_CAP - 3), 0
    width = VALUE_CAP - 6
    start = max(0, min(span[0] - 8, len(text) - width))
    end = min(len(text), start + width)
    new = ("..." if start else "") + text[start:end] + ("..." if end < len(text) else "")
    return new, (start, end), (3 if start else 0) - start


def paint(text, tokens, hls):
    """HTML for text with token spans (start, end, cls) inside highlight spans (start, end)."""
    marks = sorted({0, len(text), *[p for s, e, _ in tokens for p in (s, e)], *[p for s, e in hls for p in (s, e)]})
    out, open_hl = [], False
    for a, b in zip(marks, marks[1:]):
        if a >= b:
            continue
        in_hl = any(s <= a and b <= e for s, e in hls)
        if in_hl and not open_hl:
            out.append('<span class="hl">')
        elif not in_hl and open_hl:
            out.append("</span>")
        open_hl = in_hl
        cls = next((c for s, e, c in tokens if s <= a and b <= e), None)
        piece = he(text[a:b])
        out.append(f'<span class="{cls}">{piece}</span>' if cls else piece)
    if open_hl:
        out.append("</span>")
    return "".join(out)


def yaml_tokens(t):
    """Token spans for one shown YAML line (dash, key, value)."""
    toks, off = [], 0
    if t.startswith("- "):
        toks.append((0, 1, "d"))
        off = 2
    m = KEY_RE.match(t)
    if m:
        k = m.group(2)
        toks.append((off, off + len(k), "k"))
        val = m.group(3)
        if val and k != "condition":
            vs = len(t) - len(val)
            toks.append((vs, len(t), "n" if re.fullmatch(r"-?\d+(\.\d+)?", val) else "s"))
    elif off:
        toks.append((off, len(t), "n" if re.fullmatch(r"-?\d+", t[off:]) else "s"))
    return toks


def kql_tokens(t):
    toks = [(m.start(), m.end(), "s") for m in QUOTED_RE.finditer(t)]
    m = re.match(r"\| (\w[\w-]*)", t)
    if m:
        toks.append((0, 1, "d"))
        toks.append((m.start(1), m.end(1), "k"))
    return toks


def line_html(indent, inner, dim=False):
    cls = "ln c-dim" if dim else "ln"
    return f'<div class="{cls}">{" " * indent}{inner}</div>'


def render_example(n, ex):
    i8 = " " * 16
    lvl = ex["level"]
    pill = (f'<span class="tr-lvl tr-lvl-{lvl} font-mono">level: {lvl}</span>' if lvl
            else '<span class="tr-lvl tr-lvl-kql font-mono">KQL</span>')
    tag = (f'<div class="tr-tag font-mono">tag: attack.{ex["tid"].lower()}</div>' if ex["engine"] == "sigma"
           else '<div class="tr-tag font-mono">hunting query</div>')
    meta = "synthetic event · Claims Ledger" if ex["engine"] == "sigma" else "synthetic row · not executed"
    ok = "tr-ok" if ex["engine"] == "sigma" else "tr-ok tr-ok-pending"
    folder, _, fname = ex["file"].rpartition("/")
    parts = [
        f'{i8}<!-- {he(ex["file"])} -->',
        f'{i8}<div class="tr-ex{" is-active" if n == 0 else ""}" data-tr-ex data-tr-id="{ex["tid"]}">',
        f'{i8}    <div class="tr-panel tr-tech">',
        f'{i8}        <div class="tr-label"><span>Technique</span><span class="tr-meta">MITRE ATT&amp;CK</span></div>',
        f'{i8}        <div class="tr-id font-mono">{ex["tid"]}</div>',
        f'{i8}        <div class="tr-name">{he(ex["tname"])}</div>',
        f'{i8}        <div class="tr-tactic"><span class="tr-pill font-mono">{he(ex["tactic"])}</span></div>',
        f'{i8}        {tag}',
        f'{i8}    </div>',
        f'{i8}    <div class="tr-panel tr-trace">',
        f'{i8}        <div class="tr-label"><span>Trace</span><span class="tr-meta">{meta}</span></div>',
        f'{i8}        <div class="tr-code font-mono">',
        *[f"{i8}            {ln}" for ln in ex["event_html"]],
        f'{i8}        </div>',
        f'{i8}        <div class="tr-foot font-mono"><span class="{ok}"></span><span class="tr-expect">expect: match</span>'
        f'<span class="tr-sep"> · </span><span class="tr-claim">{he(ex["claim"])}</span></div>',
        f'{i8}    </div>',
        f'{i8}    <div class="tr-panel tr-rule">',
        f'{i8}        <div class="tr-label"><span>{"Rule" if ex["engine"] == "sigma" else "Query"}</span>{pill}</div>',
        f'{i8}        <div class="tr-code font-mono">',
        *[f"{i8}            {ln}" for ln in ex["rule_html"]],
        f'{i8}        </div>',
        f'{i8}        <div class="tr-foot font-mono"><span class="tr-path">{he(folder)}/</span>{he(fname)}</div>',
        f'{i8}    </div>',
        f'{i8}</div>',
    ]
    return "\n".join(parts)


# ---- one example ----------------------------------------------------------------------

def build_example(rel, row, opts, sigma_dir, claims_dir):
    path = sigma_dir / rel
    text = path.read_text(encoding="utf-8")
    name = path.name
    techs = parse_attack(row)
    if not techs:
        fail(f"{rel}: no ATT&CK technique in its README row")
    tid = opts.get("technique") or techs[0][0]
    hit = [t for t in techs if t[0] == tid]
    if not hit:
        fail(f"{rel}: technique {tid} is not in its README row")
    tname = hit[0][1]
    tactics = [t.strip() for t in html.unescape(row["tactic"]).split(" / ")]
    if opts.get("tactic"):
        tactic = opts["tactic"]
        if tactic not in tactics:
            fail(f"{rel}: tactic '{tactic}' is not in its README row ({', '.join(tactics)})")
    elif len(tactics) == 1:
        tactic = tactics[0]
    elif len(tactics) == len(techs):
        tactic = tactics[techs.index(hit[0])]
    else:
        fail(f"{rel}: pick a tactic for {tid} in hero-reel.json (row has {', '.join(tactics)})")

    claims_path = claims_dir / (path.stem + ".yml")
    if not claims_path.exists():
        fail(f"no claims file detections/claims/{claims_path.name}")
    claim_id, event, more, engine = load_claim(claims_path, opts.get("claim"), opts.get("event", 0))

    if engine == "kusto":
        lines, level = kql_lines(text), None
    else:
        if not re.search(rf"^\s*- attack\.{re.escape(tid.lower())}\s*$", text, re.MULTILINE):
            fail(f"{rel}: no tag line '- attack.{tid.lower()}'")
        m = re.search(r"^level: (\w+)\s*$", text, re.MULTILINE)
        if not m:
            fail(f"{rel}: no level line")
        level = m.group(1)
        lines = yaml_block(text, "correlation") or yaml_block(text, "detection")
        if not lines:
            fail(f"{rel}: no detection block")

    # matches between the event and the rule
    hl_fields = set(opts["highlight"]) if "highlight" in opts else None
    hits = []  # (rule line, span in it, event field, span in its value)
    if engine == "kusto":
        for i, span, field, vspan in kql_hits(lines, event):
            if hl_fields is None or field in hl_fields:
                hits.append((i, span, field, vspan))
    else:
        for i, field, mods, lit, span in sigma_literals(lines):
            if field not in event or field == "_synthetic":
                continue
            if hl_fields is not None and field not in hl_fields:
                continue
            if hl_fields is None and field in QUIET:
                continue
            got = sigma_hit(mods, lit, value_text(event[field]))
            if got:
                hits.append((i, span, field, got))
    rule_hl = {i for i, _, _, _ in hits}

    # which rule lines to show
    if "rule_lines" in opts:
        rows = manual_lines(lines, opts["rule_lines"], rel)
    elif engine == "kusto" and (not rule_hl or max(rule_hl) < KQL_CAP - 1):
        rows = with_gaps(lines, list(range(len(lines) if len(lines) <= KQL_CAP else KQL_CAP - 1)))
    else:
        keep = set(rule_hl) | ({0} if engine == "kusto" else
                               {i for i, (ind, t) in enumerate(lines) if ind == 0 and t.startswith("condition:")})
        rows = with_gaps(lines, pick_lines(lines, keep, RULE_CAP))
    if len(rows) > RULE_CAP:
        fail(f"{rel}: {len(rows)} rule lines to show, over {RULE_CAP}; pick them with rule_lines in hero-reel.json")
    shown = {r[3] for r in rows if r[3] is not None}
    # only what is on screen is highlighted, on both sides
    hits = [h for h in hits if h[0] in shown]
    event_hl = {}
    for _, _, field, vspan in hits:
        event_hl.setdefault(field, []).append(vspan)
    if hl_fields and not hits:
        fail(f"{rel}: the highlight fields match nothing in the shown rule lines")

    # which event fields to show: _synthetic, the fields the rule names, the highlighted ones
    if "event_keys" in opts:
        keys = opts["event_keys"]
        missing = [k for k in keys if k not in event]
        if missing:
            fail(f"{rel}: claim {claim_id} has no event field {', '.join(missing)}")
    else:
        src = " ".join(lines[i][1] for i in shown)
        if engine != "kusto":
            src += " " + " ".join(t for _, t in (yaml_block(text, "detection") or []))
        named = {k for k in event if re.search(rf"(?<![\w.-]){re.escape(k)}(?![\w-])", src)}
        keys = [k for k in event if k == "_synthetic"
                or ((k in event_hl or k in named) and not EMAIL_RE.search(value_text(event[k])))]
        if len(keys) > EVENT_CAP:
            keys = [k for k in keys if k == "_synthetic" or k in event_hl] + \
                   [k for k in keys if k != "_synthetic" and k not in event_hl]
            keys = [k for k in event if k in keys[:EVENT_CAP]]
    hits = [h for h in hits if h[2] in keys]
    event_hl = {f: v for f, v in event_hl.items() if f in keys}

    event_html, lost = [], set()
    for k in keys:
        if k == "_synthetic":
            event_html.append(line_html(0, f'<span class="k">_synthetic</span>: {he(value_text(event[k]))}', True))
            continue
        shown_v, cls = fmt_value(event[k])
        q = 1 if shown_v != value_text(event[k]) else 0
        raw = sorted(set(event_hl.get(k, [])))
        cut_v, (lo, hi), shift = cut(shown_v, (raw[0][0] + q, raw[0][1] + q) if raw else None)
        spans = []
        for s, e in raw:  # every match still whole on screen; the rule drops the rest
            if lo <= s + q and e + q <= hi:
                spans.append((s + q + shift, e + q + shift))
            else:
                lost.add((k, (s, e)))
        t = f"{k}: {cut_v}"
        vs = len(k) + 2
        tokens = [(0, len(k), "k"), (vs, len(t), cls)]
        event_html.append(line_html(0, paint(t, tokens, [(vs + s, vs + e) for s, e in spans])))
    if more:
        event_html.append(line_html(0, he(more), True))

    rule_hl = {}
    for i, span, field, vspan in hits:
        if (field, vspan) not in lost:
            rule_hl.setdefault(i, []).append(span)
    tok = kql_tokens if engine == "kusto" else yaml_tokens
    rule_html = []
    for ind, t, dim, i in rows:
        if dim:
            rule_html.append(line_html(ind, "...", True))
        else:
            rule_html.append(line_html(ind, paint(t, tok(t), rule_hl.get(i, []))))


    return {
        "file": rel, "tid": tid, "tname": tname, "tactic": tactic, "engine": "kusto" if engine == "kusto" else "sigma",
        "level": level, "claim": claim_id, "event_html": event_html, "rule_html": rule_html,
    }


def render_reel(manifest_path, rows, on_disk, sigma_dir, claims_dir):
    """The AUTO:reel region: every example, then the count for the head."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_path = {r["path"]: r for r in rows}
    no_row = sorted(set(on_disk) - set(by_path))
    if no_row:
        fail("pack files with no row in the ATT&CK table in tools/sigma-pack/README.md: " + ", ".join(no_row))
    order = [e["file"] for e in data["examples"]]
    dupes = sorted({f for f in order if order.count(f) > 1})
    if dupes:
        fail(f"listed twice in hero-reel.json: {', '.join(dupes)}")
    missing = sorted(set(on_disk) - set(order))
    if missing:
        fail("pack files missing from tools/site-build/hero-reel.json: " + ", ".join(missing))
    extra = sorted(set(order) - set(on_disk))
    if extra:
        fail("hero-reel.json names files that are not in the pack: " + ", ".join(extra))
    exs = []
    for e in data["examples"]:
        opts = {k: v for k, v in e.items() if k != "file"}
        exs.append(build_example(e["file"], by_path[e["file"]], opts, sigma_dir, claims_dir))
    return exs


def source_digest(manifest_path, sigma_dir):
    """A hash of hero-reel.json and every pack file it lists. The reel carries it,
    so a clone without ../detections can still tell that a pack file changed
    after the reel was built."""
    h = hashlib.sha256(manifest_path.read_bytes())
    for e in json.loads(manifest_path.read_text(encoding="utf-8"))["examples"]:
        path = sigma_dir / e["file"]
        h.update(e["file"].encode() + b"\0" + (path.read_bytes() if path.exists() else b"(missing)"))
    return h.hexdigest()[:16]


DIGEST_RE = re.compile(r"<!-- reel source: ([0-9a-f]{16}) -->")


def render_reel_html(exs, digest):
    out = "\n" + " " * 16 + f"<!-- reel source: {digest} -->\n" + "\n\n".join(render_example(n, ex) for n, ex in enumerate(exs)) + "\n" + " " * 16
    # the site writes no en or em dashes; a claim value may hold one on purpose
    if "\u2013" in out or "\u2014" in out:
        fail("an example would show an en or em dash; pick other event fields or another claim")
    return out


def render_reel_head(exs):
    first = exs[0]
    return (f'<span class="tr-now-id" data-tr-now>{first["tid"]}</span>'
            f'<span class="tr-count"> · <span data-tr-i>01</span> / {len(exs):02d}</span>')
