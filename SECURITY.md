# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them privately via email to the maintainers.

### What to Include

- Type of vulnerability
- Full paths of affected source files
- Location of the affected code (tag/branch/commit)
- Step-by-step instructions to reproduce
- Proof-of-concept or exploit code (if possible)
- Impact assessment

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Initial Assessment:** Within 1 week
- **Fix Timeline:** Depends on severity (critical: days, high: weeks)
- **Public Disclosure:** After fix is released

## Security Best Practices

This project follows security best practices:

- **Dependency Scanning:** Automated via Safety and Bandit
- **Code Analysis:** Security rules enforced in CI/CD
- **Secrets Detection:** Pre-commit hooks prevent secret commits
- **Regular Updates:** Dependencies monitored for vulnerabilities

## Security Scanning Configuration

See `.safety-policy.yml` for vulnerability ignore policy. All ignored
vulnerabilities are documented with:
- CVE/vulnerability ID
- Justification for ignoring
- Expiration date for review
- Tracking issue reference

## Disclosure Policy

We follow coordinated disclosure:
1. Security issue reported privately
2. Fix developed and tested
3. Security advisory published
4. Fix released
5. Public disclosure after users can update

Thank you for helping keep Start Green Stay Green secure!
