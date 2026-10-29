# Security

## Protections

- Passwords use bcrypt and access tokens require the `access` token type.
- Secret keys are generated for development or required explicitly outside
  development; weak committed defaults are not accepted.
- CORS uses explicit origins and credentialed wildcard origins are rejected.
- Project, analysis, upload, file, Git, and tool operations enforce ownership
  or workspace confinement.
- ZIP uploads reject unsafe archive paths.
- Terminal execution is disabled by default and does not use a shell when
  enabled.

## Deployment requirements

Set a random `SECRET_KEY` of at least 32 characters, a strong database
password, exact `CORS_ORIGINS`, and provider credentials through a secret
manager or protected environment. Keep Redis, Qdrant, Flower, databases, and
the workspace off the public network. Run behind TLS and add rate limiting and
centralized audit logging before exposing the service.

## Remaining limitations

The API still exposes powerful repository operations to authenticated users,
and the optional terminal allowlist is not a full sandbox. GitHub token
handling and external provider calls need operational secret-management and
egress controls. Review authorization whenever a new route is added.
