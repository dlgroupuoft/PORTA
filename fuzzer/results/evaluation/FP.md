### CD-FP: L2 verifier naming convention mismatch (10 findings)
- All: sent username (e.g., `i2_logout_user`) vs granted email (e.g., `i2-logout@test.local`). Platform naming convention, not a vulnerability.
### ZT-FP: Control step failure (1 finding)
- Test could not obtain limited-scope token (HTTP 400), making scope-escalation test invalid.

### DX-FP: HTTP 500 crashes and unsupported revocation (3 findings)
- Server crashes on malformed input, revocation endpoint returns 404.

### KC-FP: Control failures and test setup issues (3 findings)

### AK-FP: Test infrastructure issues (4 findings)

### VT-FP: Test infrastructure failures (4 findings)

### LG-FP: HTTP 500 on NUL-byte input (1 finding)
