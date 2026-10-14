#!/usr/bin/env python3
"""Static review scanner for one skill directory.

Reads a skill directory (its SKILL.md entrypoint plus the files around it) and
reports *candidate* risk patterns for human review: prompt-injection wording,
credential access, writes to global agent configuration, download-and-execute,
suspicious script constructs, package lifecycle hooks and frontmatter hooks.

Design boundaries, all deliberate:

* Stdlib only, offline. The target is never imported, executed, or fetched.
* Nothing about a match is echoed back: findings carry a static rule id, a
  relative path, a line number, a fixed reason, and a context label - never
  the matched line, URL, environment value, or secret text.
* Findings are review candidates, never verdicts, and a clean scan is not a
  safety certification (see ``assessment``, which never says safe-to-install).
* Coverage is bounded (``--max-files``, ``--max-file-bytes``, ``--max-entries``)
  and honest: binary, oversize, unreadable, non-UTF-8, unknown-format files and
  the limits themselves are listed as coverage gaps, and gaps mean the scan is
  incomplete (exit 1). Directory listings are read through a bounded iterator;
  a root directory that exceeds the entry budget is refused rather than
  partially scanned.
* package.json lifecycle keys are located with ``json.loads`` (minified files
  included), so same-named keys outside ``scripts`` are not reported, and the
  script text itself is never echoed back.
* A NUL byte in the sample marks a file as binary even when the bytes happen to
  decode as UTF-8; BOM-carrying UTF-16/UTF-32 text is still decoded.
* Links are not followed: the caller may pass a root that is itself a link
  (its target becomes the authorized root), but every link or junction inside
  the root is reported as a gap instead of being read.

Exit codes: 0 scan complete (findings may still need review), 1 incomplete or
refused, 2 invalid arguments.
"""

import argparse
import codecs
import json
import os
import re
import stat
import sys

SCHEMA_VERSION = 1
DEFAULT_MAX_FILES = 500
DEFAULT_MAX_FILE_BYTES = 1024 * 1024
DEFAULT_MAX_ENTRIES = 2000
SKILL_MD_NAME = "SKILL.md"

POLICY_SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", "__pycache__", "node_modules", ".venv", "venv",
    ".tox", ".nox", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".cache",
})

CONFIDENCE_ORDER = ("low", "medium", "high")

DISCLAIMER = (
    "Static pattern scan for human review. Findings are candidates, not "
    "verdicts, and a scan without findings is not a safety certification."
)

EXTENSION_LANGUAGES = {
    "py": "python", "pyi": "python", "pyw": "python",
    "js": "javascript", "cjs": "javascript", "mjs": "javascript",
    "jsx": "javascript", "ts": "javascript", "tsx": "javascript",
    "ps1": "powershell", "psm1": "powershell", "psd1": "powershell",
    "sh": "shell", "bash": "shell", "zsh": "shell", "ksh": "shell", "dash": "shell",
    "md": "markdown", "markdown": "markdown", "mdx": "markdown", "mdc": "markdown",
}

HOOK_KEYS = frozenset({
    "hooks", "hook", "on_load", "onload", "on_start", "onstart",
    "on_install", "on_activate",
    # Hook event names that some hosts accept as top-level fields, unwrapped:
    "pretooluse", "posttooluse", "notification", "subagentstop",
    "userpromptsubmit", "precompact", "sessionstart", "sessionend",
})
COMMAND_KEYS = frozenset({
    "command", "commands", "exec", "execute", "run", "script", "scripts",
})

LIFECYCLE_SCRIPTS = ("preinstall", "install", "postinstall", "prepare")
PACKAGE_ESCALATORS = re.compile(
    r"curl|wget|\bnode\b|npm|npx|powershell|pwsh|bash|base64|https?://"
    r"|chmod|\.sh\b|\.js\b|\.ps1\b|\.bat\b|eval\(",
    re.IGNORECASE,
)

FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z][\w-]*):\s*(.*)$")
DYNAMIC_COMMAND_RE = re.compile(r"!\s*`[^`]+`")

# Cue words that mark a line as an example rendered in documentation. They
# lower confidence but never remove a finding.
EXAMPLE_CUE_RE = re.compile(
    r"\b(?:example|examples|sample|fixture|illustration|demonstration|demonstrates"
    r"|do not run|never run|must not run|unsafe|anti-?pattern|hypothetical"
    r"|illustrative|red team)\b"
    r"|示例|例如|举例|反例|不要运行|不要执行|请勿运行|勿执行|仅用于测试|演示|对照",
    re.IGNORECASE,
)

CREDENTIAL_SOURCES = (
    r"os\.environ|os\.getenv|getenv\s*\(|process\.env|\$env:"
    r"|GetEnvironmentVariable|\.ssh[\\/]|\.aws[\\/]credentials|\.netrc\b"
    r"|id_rsa|\.git-credentials"
)
NETWORK_SENDS = (
    r"curl[^\n]{0,60}(?:-d\b|--data|-F\b|--form|-T\b|--upload-file|-X\s*POST)"
    r"|wget[^\n]{0,60}--post-data"
    r"|requests\.post"
    r"|urllib[^\n]{0,40}urlopen\s*\([^\n]{0,40}(?:data|body)"
    r"|Invoke-RestMethod[^\n]{0,60}-Method\s+Post"
    r"|fetch\s*\([^\n]{0,80}method\s*:\s*[\"']POST"
    r"|net\.connect|/dev/tcp/"
)
DOWNLOAD_EXECUTE_FORMS = (
    r"\b(?:curl|wget)\b[^\n|]{0,200}\|\s*(?:sudo\s+)?"
    r"(?:bash|sh|zsh|dash|ksh|python3?|node|perl|ruby|php|pwsh|powershell)\b"
    r"|\b(?:curl|wget|iwr|Invoke-WebRequest|Invoke-RestMethod)\b[^\n|]{0,200}"
    r"\|\s*(?:iex|Invoke-Expression)\b"
    r"|\b(?:iex|Invoke-Expression)\b[^\n]{0,60}"
    r"(?:iwr|Invoke-WebRequest|DownloadString|DownloadFile|Net\.WebClient)"
    r"|(?:DownloadString|DownloadFile|Net\.WebClient)[^\n]{0,120}"
    r"(?:iex|Invoke-Expression)\b"
    r"|\b(?:bash|sh|zsh|pwsh|powershell|python3?)\b[^\n]{0,10}-c\s*[\"']?\$\((?:curl|wget)\b"
    r"|\bmshta(?:\.exe)?\s+[\"']?(?:https?://|javascript:)"
    r"|\bcertutil\b[^\n]{0,80}(?:-urlcache|-decode)[^\n]{0,80}https?://"
)
OBFUSCATED_FORMS = (
    r"-(?:enc|encodedcommand)\b[^\n]{0,40}\b[A-Za-z0-9+/]{40,}={0,2}"
    r"|\s-e\s+[A-Za-z0-9+/]{60,}={0,2}"
    r"|(?:FromBase64String|base64\.b64decode|codecs\.decode)[^\n]{0,80}"
    r"(?:iex|Invoke-Expression|eval\(|exec\()"
    r"|\bbase64\s+(?:-d|--decode|-D)\b[^\n]{0,120}\|\s*(?:bash|sh|zsh|python3?|node|perl)"
    r"|\b(?:eval|exec)\s*\(\s*(?:atob|Buffer\.from\([^)]*base64|base64\.b64decode|codecs\.decode)"
)
DESTRUCTIVE_FORMS = (
    r"\brm\s+-[a-z]*[rf][a-z]*\s+(?:-[a-z]+\s+)*(?:/|~|\$HOME|\*)"
    r"|\b(?:rmdir|rd)\s+/s\s+/q\s+[a-z]:[\\/]"
    r"|\bdel\s+/[a-z]*s[a-z]*\s+/[a-z]*q[a-z]*\s+[a-z]:[\\/]"
    r"|\bRemove-Item\b[^\n]{0,80}-Recurse[^\n]{0,80}"
    r"(?:[a-z]:[\\/]\s*$|~|\$HOME|%USERPROFILE%|[\"']?/\s*$)"
    r"|shutil\.rmtree\s*\(\s*[\"'](?:/|~|\\|[a-z]:[\\/])"
    r"|\bformat\s+[a-z]:"
    r"|\bdd\b[^\n]{0,60}of=/dev/"
    r"|\bmkfs(?:\.[a-z0-9]+)?\b"
)


def _rule(rule_id, category, confidence, reason, pattern, **extra):
    spec = {
        "id": rule_id,
        "category": category,
        "confidence": confidence,
        "reason": reason,
        "matcher": re.compile(pattern, re.IGNORECASE),
    }
    spec.update(extra)
    return spec


RULES = (
    _rule(
        "instruction-override", "prompt-injection", "high",
        "Text asks the reader to ignore, forget, or override earlier instructions.",
        r"\b(?:ignore|disregard|forget|override)\b[^\n]{0,40}"
        r"\b(?:previous|prior|earlier|above|preceding)\b[^\n]{0,30}"
        r"\b(?:instructions?|prompts?|rules?|directives?)\b"
        r"|(?:忽略|无视|忘记|覆盖|绕过)[^\n]{0,12}(?:之前|前面|以上|上面|先前)[^\n]{0,8}"
        r"(?:指令|规则|要求|提示词|限制)",
    ),
    _rule(
        "instruction-concealment", "prompt-injection", "medium",
        "Text asks the reader to hide actions or information from the user.",
        r"\b(?:do not|don'?t|never)\s+(?:tell|inform|notify|show|reveal)\b[^\n]{0,30}"
        r"\b(?:user|human)\b"
        r"|\b(?:hide|conceal)\b[^\n]{0,30}\bfrom\s+(?:the\s+)?(?:user|human)\b"
        r"|(?:不要|别|勿|不得)(?:告诉|告知|提醒|通知)(?:用户|人类)",
    ),
    _rule(
        "instruction-extraction", "prompt-injection", "medium",
        "Text asks the reader to reveal system or hidden instructions.",
        r"\b(?:print|show|reveal|output|repeat|dump|leak)\b[^\n]{0,30}"
        r"\b(?:system prompt|system message|hidden instructions|your instructions|your prompt)\b"
        r"|(?:输出|显示|泄露|打印|重复)[^\n]{0,10}(?:系统提示词|系统提示|你的指令|你的规则|隐藏指令)",
    ),
    _rule(
        "invisible-unicode", "obfuscation", "medium",
        "Line contains invisible or bidirectional Unicode control characters.",
        r"[\u200b\u200c\u202a-\u202e\u2060\u2066-\u2069\ufeff]",
    ),
    _rule(
        "credential-private-key", "credential-access", "high",
        "References a private key or SSH key path.",
        r"\.ssh[\\/]id_(?:rsa|dsa|ecdsa|ed25519)\b|\bid_(?:rsa|dsa|ecdsa|ed25519)\b",
    ),
    _rule(
        "credential-store", "credential-access", "medium",
        "References a saved credential store or a credential lookup command.",
        r"\.aws[\\/]credentials\b|\.netrc\b|_netrc\b|\.git-credentials\b"
        r"|\.docker[\\/]config\.json|\.kube[\\/]config\b|Microsoft[\\/]Credentials\b"
        r"|\bLogin Data\b|security\s+find-(?:generic|internet)-password\b"
        r"|\bGet-StoredCredential\b|cmdkey[^\n]{0,20}/list\b",
    ),
    _rule(
        "env-secret-read", "credential-access", "medium",
        "Reads an environment variable whose name looks like a secret.",
        r"os\.environ|os\.getenv|getenv\s*\(|process\.env|\$env:|GetEnvironmentVariable",
        also=r"TOKEN|SECRET|PASSWORD|PASSWD|API[_-]?KEY|PRIVATE[_-]?KEY|CREDENTIAL",
    ),
    _rule(
        "exfiltration-combined", "credential-access", "medium",
        "Combines a credential-like source with a network send in one line.",
        CREDENTIAL_SOURCES,
        also=NETWORK_SENDS,
    ),
    _rule(
        "global-agent-config-write", "agent-config", "medium",
        "Writes to a global agent or editor configuration path.",
        r"\.claude\b|\.cursor\b|\.codex\b|\.agents[\\/]|\.gemini\b"
        r"|AppData[\\/]Roaming[\\/](?:Claude|Cursor|Codex)\b"
        r"|(?:^|[\\/'\s])(?:CLAUDE|AGENTS)\.md\b|mcp\.json\b",
        also=r"Set-Content|Add-Content|Out-File|Copy-Item|Move-Item|New-Item|Remove-Item"
             r"|writeFile|writeFileSync|appendFile|write_text|shutil\.copy"
             r"|open\([^\n]{0,40}[\"'][wa][\"']|>>\s*|\b(?:cp|mv|tee)\s",
    ),
    _rule(
        "download-execute", "execution", "high",
        "Fetches remote content and pipes it into an interpreter or evaluator.",
        DOWNLOAD_EXECUTE_FORMS,
    ),
    _rule(
        "obfuscated-execution", "obfuscation", "high",
        "Executes encoded or decoded payload text.",
        OBFUSCATED_FORMS,
    ),
    _rule(
        "unsafe-deserialization", "execution", "medium",
        "Deserialises data with a format that can execute code.",
        r"\b(?:marshal|cPickle|pickle)\.loads\s*\(|\byaml\.unsafe_load\s*\(",
    ),
    _rule(
        "destructive-filesystem", "destructive-operations", "medium",
        "Deletes or overwrites a root, home, or whole-disk target.",
        DESTRUCTIVE_FORMS,
    ),
    _rule(
        "package-install-from-url", "supply-chain", "medium",
        "Installs a dependency directly from a URL or git endpoint.",
        r"\b(?:pip|pip3|uv)\s+(?:install|add)\s+(?:git\+|https?://)"
        r"|npm\s+(?:i|install|add)\s+(?:https?://|git\+)"
        r"|(?:yarn|pnpm)\s+add\s+(?:https?://|git\+)"
        r"|npx\s+https?://|deno\s+(?:run|install)\s+https?://",
    ),
    _rule(
        "python-dynamic-exec", "execution", "medium",
        "Python file calls eval or exec.",
        r"(?<![\w.])(?:eval|exec)\s*\(",
        languages=frozenset({"python"}),
    ),
    _rule(
        "python-subprocess-shell", "execution", "medium",
        "Python file runs a subprocess through a shell.",
        r"subprocess\.(?:run|call|check_call|check_output|Popen|getoutput|getstatusoutput)"
        r"\s*\([^\n]*shell\s*=\s*True",
        languages=frozenset({"python"}),
    ),
    _rule(
        "python-os-command", "execution", "medium",
        "Python file invokes an OS command.",
        r"\bos\.(?:system|popen|spawnl|spawnlp|spawnv|spawnvp|execv|execvp|execl|execlp)\s*\(",
        languages=frozenset({"python"}),
    ),
    _rule(
        "js-child-process", "execution", "medium",
        "JavaScript file spawns a child process.",
        r"\b(?:exec|execSync|spawn|spawnSync|execFile)\s*\(",
        also=r"child_process",
        languages=frozenset({"javascript"}),
    ),
    _rule(
        "js-dynamic-exec", "execution", "medium",
        "JavaScript file calls eval or new Function.",
        r"(?<![\w.])(?:eval|new\s+Function)\s*\(",
        languages=frozenset({"javascript"}),
    ),
    _rule(
        "ps-invoke-expression", "execution", "medium",
        "PowerShell file evaluates a string as code.",
        r"\bInvoke-Expression\b|\biex\b",
        languages=frozenset({"powershell"}),
    ),
    _rule(
        "ps-policy-bypass", "execution", "low",
        "PowerShell invocation bypasses the execution policy.",
        r"-executionpolicy\s+(?:bypass|unrestricted)",
        languages=frozenset({"powershell"}),
    ),
    _rule(
        "shell-eval", "execution", "medium",
        "Shell file evaluates a constructed string as code.",
        r"\beval\s+[\"'$]|\beval\s+\$\(",
        languages=frozenset({"shell"}),
    ),
    _rule(
        "dynamic-command", "dynamic-content", "medium",
        "Line embeds a dynamic !-command whose output would be inlined.",
        r"!\s*`[^`]+`",
        agent_doc=True,
        body_only=True,
    ),
)

FRONTMATTER_RULES = (
    {
        "id": "frontmatter-hook-field",
        "category": "dynamic-frontmatter",
        "confidence": "medium",
        "reason": "Skill frontmatter declares a lifecycle hook.",
        "kind": "keys",
        "keys": HOOK_KEYS,
    },
    {
        "id": "frontmatter-command-field",
        "category": "dynamic-frontmatter",
        "confidence": "medium",
        "reason": "Skill frontmatter declares a command that may run automatically.",
        "kind": "keys",
        "keys": COMMAND_KEYS,
    },
    {
        "id": "frontmatter-dynamic-command",
        "category": "dynamic-frontmatter",
        "confidence": "medium",
        "reason": "Skill frontmatter embeds a dynamic !-command.",
        "kind": "pattern",
        "matcher": DYNAMIC_COMMAND_RE,
    },
)


# --------------------------------------------------------------------- paths


def _posix_rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def _entry_is_link(entry):
    try:
        if entry.is_symlink():
            return True
        # Reject every Windows reparse point, including junctions on Python
        # versions that do not expose os.path.isjunction. Fail closed on I/O.
        info = entry.stat(follow_symlinks=False)
        if getattr(info, "st_file_attributes", 0) & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            return True
        isjunction = getattr(os.path, "isjunction", None)
        return bool(isjunction and isjunction(entry.path))
    except OSError:
        return True


def _entry_is_dir(entry):
    try:
        return entry.is_dir(follow_symlinks=False)
    except OSError:
        return False


def _sort_key(entry):
    return (entry.name.casefold(), entry.name)


def _split_extension(name):
    index = name.rfind(".")
    if index <= 0:
        return name, ""
    return name[:index], name[index + 1:].lower()


def _detect_language(name, first_line):
    _, extension = _split_extension(name)
    if extension in EXTENSION_LANGUAGES:
        return EXTENSION_LANGUAGES[extension]
    if first_line.startswith("#!"):
        probe = first_line.lower()
        if "python" in probe:
            return "python"
        if "node" in probe or "deno" in probe or "bun" in probe:
            return "javascript"
        if "pwsh" in probe or "powershell" in probe:
            return "powershell"
        if re.search(r"(?:^|[/\s])(?:bash|sh|zsh|ksh|dash)\b", probe):
            return "shell"
    return "text"


def _decode_text(raw):
    """Return (text, None) for decodable text, (None, reason) otherwise.

    BOM-carrying UTF-16/UTF-32 is decoded first. For everything else a NUL byte
    means binary, even when the raw bytes would decode as UTF-8: NUL is a valid
    UTF-8 codepoint, so ``b"MZ\\x00payload"`` must not count as scanned text.
    """
    if raw.startswith(codecs.BOM_UTF32_LE) or raw.startswith(codecs.BOM_UTF32_BE):
        return _try_decode(raw, "utf-32")
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        return _try_decode(raw, "utf-16")
    if raw.startswith(codecs.BOM_UTF8):
        return _try_decode(raw, "utf-8-sig")
    if b"\x00" in raw:
        return None, "binary"
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        pass
    try:
        raw.decode("cp936")
    except (UnicodeDecodeError, LookupError):
        return None, "binary"
    return None, "unknown-format"


def _try_decode(raw, encoding):
    try:
        text = raw.decode(encoding)
        if "\x00" in text:
            return None, "binary"
        return text, None
    except (UnicodeDecodeError, LookupError):
        return None, "unknown-format"


def _enumerate(path, remaining):
    """Read at most ``remaining`` directory entries, peeking one more to detect more."""
    remaining = max(0, remaining)
    entries = []
    truncated = False
    with os.scandir(path) as iterator:
        for entry in iterator:
            if len(entries) == remaining:
                truncated = True
                break
            entries.append(entry)
    return entries, truncated


def _resolve_skill_entry(entries):
    exact = [entry for entry in entries if entry.name == SKILL_MD_NAME]
    candidates = exact or [
        entry for entry in entries if entry.name.casefold() == SKILL_MD_NAME.casefold()
    ]
    if not candidates:
        return None, "no-skill-md"
    if len(candidates) > 1:
        return None, "ambiguous-skill-md"
    entry = candidates[0]
    if _entry_is_link(entry) or not entry.is_file(follow_symlinks=False):
        return None, "skill-md-not-regular"
    return entry, None


# ------------------------------------------------------------------- scanning


def _rule_applies(rule, language, name, in_frontmatter):
    if rule.get("body_only") and in_frontmatter:
        return False
    if rule.get("agent_doc") and not (
        language == "markdown" or name.casefold() == SKILL_MD_NAME.casefold()
    ):
        return False
    languages = rule.get("languages")
    if languages is not None and language not in languages:
        return False
    return True


def _lower_confidence(confidence, context):
    if not context:
        return confidence
    return CONFIDENCE_ORDER[max(0, CONFIDENCE_ORDER.index(confidence) - 1)]


def _context_for(lines, number, in_fence):
    window = lines[max(0, number - 2):number + 1]
    for part in window:
        # Cue words inside a URL ("example.com/...") are not documentation
        # markers, so strip URL tokens before probing.
        probe = re.sub(r"\S*://\S+", " ", part)
        if EXAMPLE_CUE_RE.search(probe):
            return "documentation-example"
    if in_fence:
        return "markdown-code-block"
    return None


def _finding(rule_id, category, confidence, reason, rel, number, context):
    return {
        "ruleId": rule_id,
        "category": category,
        "file": rel,
        "line": number,
        "confidence": confidence,
        "context": context,
        "reason": reason,
    }


def _frontmatter_bounds(lines):
    """Return the inclusive 1-based line range of frontmatter content, or None."""
    if not lines or lines[0].strip() != "---":
        return None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return (2, index)
    return None


def _scan_frontmatter(lines, rel):
    bounds = _frontmatter_bounds(lines)
    if bounds is None:
        return []
    last = bounds[1]
    findings = []
    for number in range(2, last + 1):
        line = lines[number - 1]
        key_match = FRONTMATTER_KEY_RE.match(line)
        if key_match:
            key = key_match.group(1).lower()
            value = key_match.group(2).strip()
            if not value and number + 1 <= last:
                continuation = lines[number]
                value = continuation.strip() if continuation[:1].isspace() else ""
            for rule in FRONTMATTER_RULES:
                if rule["kind"] == "keys" and key in rule["keys"] and value:
                    findings.append(_finding(
                        rule["id"], rule["category"], rule["confidence"],
                        rule["reason"], rel, number, None))
        for rule in FRONTMATTER_RULES:
            if rule["kind"] == "pattern" and rule["matcher"].search(line):
                findings.append(_finding(
                    rule["id"], rule["category"], rule["confidence"],
                    rule["reason"], rel, number, None))
    return findings


def _locate_key_line(text, key, start):
    pattern = re.compile(r'"%s"\s*:' % re.escape(key))
    match = pattern.search(text, start)
    if match is None:
        match = pattern.search(text)
    if match is None:
        return 1
    return text.count("\n", 0, match.start()) + 1


def _scan_package_json(text, rel):
    """Inspect package.json scripts with json.loads; returns (findings, gap)."""
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        return [], "invalid-json"
    if not isinstance(data, dict):
        return [], None
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return [], None
    marker = re.search(r'"scripts"\s*:', text)
    search_from = marker.start() if marker else 0
    findings = []
    for key in LIFECYCLE_SCRIPTS:
        if key not in scripts:
            continue
        value = scripts[key]
        escalated = isinstance(value, str) and PACKAGE_ESCALATORS.search(value)
        findings.append(_finding(
            "package-lifecycle-script", "supply-chain",
            "high" if escalated else "medium",
            "package.json lifecycle script will run when the skill is installed.",
            rel, _locate_key_line(text, key, search_from), None))
    return findings, None


def _scan_text(text, rel, name):
    """Return (findings, gap_reason_or_None) for one decoded file."""
    lines = re.split(r"\r\n|\r|\n", text)
    language = _detect_language(name, lines[0] if lines else "")
    is_markdown = language == "markdown"
    is_agent_doc = is_markdown or name.casefold() == SKILL_MD_NAME.casefold()
    bounds = _frontmatter_bounds(lines) if is_agent_doc else None
    findings = []
    seen = set()
    in_fence = False
    for number, line in enumerate(lines, 1):
        if is_markdown and FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        in_frontmatter = bounds is not None and bounds[0] <= number <= bounds[1]
        for rule in RULES:
            if not _rule_applies(rule, language, name, in_frontmatter):
                continue
            key = (rule["id"], number)
            if key in seen or not rule["matcher"].search(line):
                continue
            also = rule.get("also")
            if also is not None and not re.search(also, line, re.IGNORECASE):
                continue
            seen.add(key)
            context = _context_for(lines, number, in_fence)
            findings.append(_finding(
                rule["id"], rule["category"],
                _lower_confidence(rule["confidence"], context),
                rule["reason"], rel, number, context))
    gap_reason = None
    if name.casefold() == "package.json":
        package_findings, gap_reason = _scan_package_json(text, rel)
        findings.extend(package_findings)
    if is_agent_doc:
        findings.extend(_scan_frontmatter(lines, rel))
    return findings, gap_reason


def _walk(root, skill_entry, root_entries, max_files, max_file_bytes, max_entries):
    findings, gaps, policy_skips = [], [], []
    limits_hit = {"file": False, "entry": False}
    state = {"examined": 0, "scanned": 0, "visited": len(root_entries)}

    def process(entry):
        state["examined"] += 1
        rel = _posix_rel(entry.path, root)
        try:
            info = entry.stat(follow_symlinks=False)
        except OSError:
            gaps.append({"path": rel, "reason": "unreadable"})
            return
        if not stat.S_ISREG(info.st_mode):
            gaps.append({"path": rel, "reason": "special-file"})
            return
        try:
            with open(entry.path, "rb") as handle:
                raw = handle.read(max_file_bytes + 1)
        except OSError:
            gaps.append({"path": rel, "reason": "unreadable"})
            return
        if len(raw) > max_file_bytes:
            gaps.append({"path": rel, "reason": "oversize"})
            return
        text, gap_reason = _decode_text(raw)
        if text is None:
            gaps.append({"path": rel, "reason": gap_reason})
            return
        state["scanned"] += 1
        file_findings, file_gap = _scan_text(text, rel, entry.name)
        findings.extend(file_findings)
        if file_gap is not None:
            gaps.append({"path": rel, "reason": file_gap})

    process(skill_entry)

    pending = [(root, root_entries)]
    while pending and not limits_hit["file"] and not limits_hit["entry"]:
        current, entries = pending.pop()
        if entries is None:
            try:
                entries, truncated = _enumerate(current, max_entries - state["visited"])
            except OSError:
                gaps.append({"path": _posix_rel(current, root), "reason": "unreadable"})
                continue
            state["visited"] += len(entries)
            if truncated:
                limits_hit["entry"] = True
                gaps.append({"path": _posix_rel(current, root), "reason": "entry-limit"})
                break
        for entry in entries:
            if current == root and entry.name == skill_entry.name:
                continue
            is_link = _entry_is_link(entry)
            is_dir = (not is_link) and _entry_is_dir(entry)
            if is_dir and entry.name.casefold() in POLICY_SKIP_DIRS:
                policy_skips.append(_posix_rel(entry.path, root))
                continue
            if state["examined"] >= max_files:
                limits_hit["file"] = True
                gaps.append({"path": _posix_rel(entry.path, root), "reason": "file-limit"})
                break
            if is_link:
                state["examined"] += 1
                gaps.append({"path": _posix_rel(entry.path, root), "reason": "internal-link"})
                continue
            if is_dir:
                pending.append((entry.path, None))
                continue
            process(entry)
    examined = state["examined"]
    scanned = state["scanned"]
    return findings, gaps, sorted(policy_skips), scanned, examined, state["visited"]


def _envelope(max_files, max_file_bytes, max_entries):
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "refused",
        "refusal": None,
        "findings": [],
        "coverage": {
            "complete": False,
            "scannedFiles": 0,
            "examinedFiles": 0,
            "visitedEntries": 0,
            "gaps": [],
            "policySkips": [],
            "limits": {
                "maxFiles": max_files,
                "maxFileBytes": max_file_bytes,
                "maxEntries": max_entries,
            },
        },
        "assessment": "review-required",
        "disclaimer": DISCLAIMER,
    }


def scan(root_arg, max_files, max_file_bytes, max_entries):
    result = _envelope(max_files, max_file_bytes, max_entries)
    resolved = os.path.realpath(os.path.abspath(root_arg))
    if not os.path.exists(resolved):
        result["refusal"] = "root-missing"
        return result
    if not os.path.isdir(resolved):
        result["refusal"] = "root-not-directory"
        return result
    try:
        root_entries, truncated = _enumerate(resolved, max_entries)
    except OSError:
        result["refusal"] = "root-unreadable"
        return result
    result["coverage"]["visitedEntries"] = len(root_entries)
    if truncated:
        result["refusal"] = "root-entry-limit"
        return result
    skill_entry, refusal = _resolve_skill_entry(root_entries)
    if refusal is not None:
        result["refusal"] = refusal
        return result
    findings, gaps, policy_skips, scanned, examined, visited = _walk(
        resolved, skill_entry, root_entries, max_files, max_file_bytes, max_entries)
    coverage = result["coverage"]
    coverage["scannedFiles"] = scanned
    coverage["examinedFiles"] = examined
    coverage["visitedEntries"] = visited
    coverage["gaps"] = gaps
    coverage["policySkips"] = policy_skips
    coverage["complete"] = not gaps
    result["findings"] = sorted(findings, key=lambda item: (item["file"], item["line"], item["ruleId"]))
    result["status"] = "ok" if coverage["complete"] else "incomplete"
    if result["findings"] or not coverage["complete"]:
        result["assessment"] = "review-required"
    else:
        result["assessment"] = "no-findings-detected"
    return result


# ----------------------------------------------------------------------- cli


def positive_int(text):
    try:
        value = int(text)
    except ValueError:
        value = 0
    if value <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return value


def build_parser():
    parser = argparse.ArgumentParser(
        prog="scan_skill.py",
        description=(
            "Statically scan one skill directory and print a JSON report to stdout. "
            "The target is never executed, imported, or fetched; findings are review "
            "candidates, not verdicts."
        ),
        epilog=(
            "exit codes: 0 scan complete (findings may still need review); "
            "1 scan incomplete or refused; 2 invalid arguments."
        ),
    )
    parser.add_argument("directory", help="skill directory that contains a regular SKILL.md")
    parser.add_argument("--max-files", type=positive_int, default=DEFAULT_MAX_FILES,
                        metavar="N", help="inspect at most N files (default: %(default)s)")
    parser.add_argument("--max-file-bytes", type=positive_int, default=DEFAULT_MAX_FILE_BYTES,
                        metavar="N", help="read at most N bytes per file (default: %(default)s)")
    parser.add_argument("--max-entries", type=positive_int, default=DEFAULT_MAX_ENTRIES,
                        metavar="N", help="enumerate at most N directory entries (default: %(default)s)")
    return parser


def _write_json(payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    stream = sys.stdout
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (ValueError, OSError):
            pass
    stream.write(text)
    stream.flush()


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = scan(args.directory, args.max_files, args.max_file_bytes, args.max_entries)
    except Exception:  # never leak internals, paths, or tracebacks into the report
        result = _envelope(args.max_files, args.max_file_bytes, args.max_entries)
        result["refusal"] = "internal-error"
    _write_json(result)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
