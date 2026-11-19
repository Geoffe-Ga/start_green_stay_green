---
name: security
description: >-
  Implement secure coding practices against common vulnerabilities.
  Use when handling user input, file paths, subprocess calls, SQL queries,
  API keys, or building web endpoints. Covers input validation, injection
  prevention, secret management, and XSS/CSRF protection across Python,
  TypeScript, Go, and Rust. Do NOT use for general error handling
  (use error-handling skill) or for remediating dependency vulnerability
  scanner failures and CVE / GHSA advisories (use cve-remediation skill).
metadata:
  author: Geoff
  version: 1.1.0
---

# Security

Defense in depth, least privilege, fail securely, never trust user input.

## Instructions

### Step 1: Follow the Principles

1. Defense in depth - multiple layers of security
2. Least privilege - minimal access required
3. Fail securely - errors don't expose sensitive data
4. Input validation at all boundaries
5. Never trust user input
6. Secure by default, not by configuration

### Step 2: Apply Security Patterns

See `references/patterns-by-language.md` for language-specific implementations.

Key areas:
- **Input validation**: Allowlist characters, validate format, limit length
- **Path traversal prevention**: Resolve paths, verify within base directory
- **Command injection prevention**: Never use `shell=True`, validate arguments
- **SQL injection prevention**: Always use parameterized queries
- **XSS prevention**: Escape HTML output, use framework defaults
- **Secret management**: Use OS keyring, never hardcode secrets
- **CSRF protection**: Use tokens with constant-time comparison
- **User-supplied API keys/credentials**: never store them server-side in
  plaintext (client-side secure storage or an encrypted-at-rest store); pass
  via a request header, never a URL or body; never log the value or echo it
  back in a response; validate its format before forwarding; clear from
  memory after use
- **Error responses**: never surface an internal exception's message or
  traceback to the caller — log the detail server-side, return a generic
  message (see Example 3)

### Step 3: Run the Security Checklist

Before deploying:

**Input and injection**
- [ ] All user inputs validated at boundaries (schema/validation models, allowlists)
- [ ] Request body size limits enforced
- [ ] No SQL injection (parameterized queries / ORM, no string-built SQL)
- [ ] No command injection (no `shell=True`)
- [ ] No path traversal (validated file paths)
- [ ] No XSS (escaped HTML)

**Authentication and authorization** (if the app has accounts)
- [ ] Session/auth tokens expire (short TTL, refresh flow if needed)
- [ ] Signing keys are cryptographically random, never a placeholder default
- [ ] Passwords hashed with a slow, salted algorithm (bcrypt/argon2/scrypt) at an adequate work factor
- [ ] Rate limiting and lockout on auth endpoints
- [ ] Auth failures return a generic message ("invalid credentials") with no user-enumeration or timing tell
- [ ] Every id in a request that references another user's object is ownership-checked

**API and transport**
- [ ] CORS restricted to specific origins (never `*` with credentials)
- [ ] HTTPS for all external requests; HSTS in production
- [ ] SSL certificates validated
- [ ] Security headers set (e.g. `X-Content-Type-Options`, `X-Frame-Options` / CSP)
- [ ] No debug endpoints or debug mode in production
- [ ] Responses don't expose sensitive fields (hashes, tokens, internal ids)
- [ ] Error messages don't leak sensitive data

**Secrets**
- [ ] API keys in OS keyring or a secret manager, not code
- [ ] Secrets not committed to git (`.env` in `.gitignore`, secret-scanner baseline current)
- [ ] Logging doesn't include secrets or PII

**Dependencies and deployment**
- [ ] Dependency audit clean (see the cve-remediation skill for failures)
- [ ] Containers use minimal base images and run as a non-root user
- [ ] Database credentials come from the environment/secret store only

## Examples

See `references/examples.md` for complete worked examples.

### Example 1: Safe Path Handling (Python)

```python
def safe_path_join(base_dir: Path, user_path: str) -> Path:
    base_dir = base_dir.resolve()
    target = (base_dir / user_path).resolve()
    try:
        target.relative_to(base_dir)
    except ValueError:
        raise ValueError(f"Path traversal detected: {user_path!r}") from None
    return target
```

### Example 2: Safe Subprocess Call (Python)

```python
# WRONG - shell injection vulnerability
subprocess.run(f"git clone {user_repo}", shell=True)

# CORRECT - no injection possible
subprocess.run(["git", "clone", user_repo], check=True)
```

### Example 3: Safe Error Response (any web framework)

```python
# WRONG - leaks internal details (stack trace, query, file paths) to the caller
raise HTTPException(status_code=500, detail=str(exc))

# CORRECT - log the detail server-side, return a generic message
logger.exception("Unhandled error in endpoint X")
raise HTTPException(status_code=500, detail="internal_error")
```

## Troubleshooting

### Error: Keyring not available in CI/headless environment
- Use environment variables as fallback for CI only
- Document the fallback in CI configuration
- Never use environment variables for production secret storage

### Error: Secret scanner flags a false positive
- Re-audit and update the baseline (e.g. `detect-secrets scan --baseline .secrets.baseline`)
- Use an inline `# pragma: allowlist secret` only on test fixtures with obviously fake values
- Never allowlist a value that could be a real credential: rotate it instead

### Error: Path validation too restrictive
- Check if you're resolving symlinks unnecessarily
- Verify the base directory itself is resolved before comparison
- Test with both relative and absolute user paths
