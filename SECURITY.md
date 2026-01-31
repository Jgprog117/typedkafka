# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

1. **Do NOT** open a public issue
2. Email the maintainers directly (or use GitHub Security Advisories)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- We aim to acknowledge reports within 48 hours
- We will provide an initial assessment within 5 business days
- We will work to release a fix as quickly as possible

## Disclosure Policy

- We request that you give us reasonable time to address the issue before public disclosure
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using typedkafka:
- Always use the latest version
- Keep confluent-kafka dependency updated
- Never commit credentials or API keys
- Use environment variables for sensitive configuration

Thank you for helping keep typedkafka secure!
