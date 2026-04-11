# Security Audit Report — Lords Mobile Bot v2.0

**Audit date:** 2026-04-10  
**Auditor:** Direct code review  
**Severity scale:** Critical · High · Medium · Low · Info  

---

## Executive Summary

**Overall Severity: HIGH**

The bot has multiple security issues across several categories. Most critically:
- Historical GitHub OAuth secrets remain in git history (commit `56f6a22`)
- Web dashboard has no authentication (CORS `*`, no login)
- `debug=True` exposed in production Flask server
- Shellcode injection architecture has memory safety issues

That said, several findings are **by design** for a game bot (process injection, memory reading, packet sniffing) and are noted as such.

---

## Critical Issues

### 1. GitHub OAuth Secrets in Git History
**Severity:** 🔴 Critical  
**Type:** Secrets hardcoded / historical commit leak  

OAuth client IDs and client secrets from the original C# dump.cs were committed to the repo and later removed. Anyone who cloned before the force-push still has them. The GitHub PAT appears in workspace memory files, not in the repo itself.

**Recommendation:** Rotate the GitHub PAT immediately. Accept OAuth history leak as unavoidable for public repos.

---

### 2. Flask Web Dashboard — No Authentication
**File:** `ui/web/app.py` lines 14, 90  
**Severity:** 🔴 Critical  
**Type:** Missing authentication  

```python
socketio = SocketIO(app, cors_allowed_origins="*")
# ...
socketio.run(app, host="0.0.0.0", port=5000, debug=True)
```

Anyone on the network can read/modify bot config, trigger redemptions, control gatherer, and access the Flask debugger.

**Recommendation:** Add Flask-Login or basic HTTP auth. Restrict CORS. Disable debug mode in production.

---

### 3. Flask Debug Mode Exposes Remote Code Execution
**File:** `ui/web/app.py` line 90  
**Severity:** 🔴 Critical  
**Type:** Insecure configuration  

`debug=True` with `host="0.0.0.0"` means the Werkzeug debugger is exposed.

**Recommendation:** Set `debug=False` or use `DEBUG=False` environment variable.

---

## High Issues

### 4. Memory Safety Bug in `sniffer.py` Shellcode Builder (FIXED)
**File:** `core/network/sniffer.py`  
**Severity:** 🟠 High (now fixed)  
**Type:** Memory corruption  

The shellcode used `id(march_data)` — the Python object address, not a valid remote process address. This has been fixed to use `content_addr` allocated via `VirtualAllocEx`.

---

### 5. No Input Validation on API Endpoints
**File:** `ui/web/app.py` lines 47-53  
**Severity:** 🟠 High  
**Type:** Path traversal / arbitrary file write  

An attacker with access can overwrite any `.json` file reachable from the app's working directory.

**Recommendation:** Add path validation, require authentication, validate JSON structure.

---

## Medium Issues

### 6. Hardcoded Flask SECRET_KEY
**Severity:** 🟡 Medium  
**Recommendation:** Use `secrets.token_hex(32)` or read from environment variable.

### 7. No HTTPS
**Severity:** 🟡 Medium  
**Recommendation:** Use nginx + Let's Encrypt TLS in front of Flask.

### 8. Rate Limiting Absent from API
**Severity:** 🟡 Medium  
**Recommendation:** Add Flask-Limiter (e.g., 30 req/min per IP).

---

## Low Issues

### 9. Hardcoded Window Title
**Files:** `core/win32/hands.py`, `config/settings.json`

### 10. `except Exception` Broad Catches
**Files:** Multiple files — hides real errors.

---

## By Design (Inherent to Bot Functionality)

| Pattern | Location | Note |
|---------|----------|------|
| Shellcode injection | `modules/attacker/bot.py` | ✅ Correctly uses `VirtualAllocEx` |
| Raw socket access | `core/network/sniffer.py` | Game server communication |
| Memory reading | `core/memory/radar.py` | Win32 `ReadProcessMemory` via ctypes |
| Frida script injection | `core/frida/scripts/` | Anti-Frida detection bypass |

---

## Recommendations (Priority Order)

1. **Rotate GitHub PAT** — if exposed, revoke and create new
2. **Add authentication to Flask app** — minimum HTTP basic auth
3. **Disable debug mode** — `debug=False` in production
4. **Restrict CORS** — not `*`
5. **Add input validation** — on `/api/config` POST
6. **Use environment variable for SECRET_KEY**
7. **Add rate limiting** — Flask-Limiter

---

## Safe Patterns Already in Use

- ✅ Centralized offsets in JSON, not hardcoded
- ✅ Anti-detection uses `random.uniform` for timing
- ✅ Session guard uses sliding window rate limiting
- ✅ Human clicker uses Bezier curves
- ✅ All analytics stored locally, not sent externally
- ✅ Legacy code (with secrets) archived in `legacy/`, not in git
