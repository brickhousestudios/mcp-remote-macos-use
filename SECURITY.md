# Security Policy

## ⚠️ CRITICAL SECURITY WARNINGS

### This Tool Should NOT Be Used for Sensitive Operations

**MCP Remote macOS Use contains inherent security limitations due to the VNC protocol it relies on. Read this document carefully before use.**

---

## 🔒 Cryptographic Limitations

### Weak Encryption in Apple VNC Protocol 30

This implementation **only** supports Apple Authentication Protocol 30, which uses:

- **512-bit Diffie-Hellman Key Exchange** - Vulnerable to modern attacks, considered cryptographically weak
- **MD5 Hashing** - Broken hash algorithm, NOT suitable for security purposes
- **Single DES Encryption** - Deprecated cipher, easily broken with modern computing
- **AES in ECB Mode** - Does not provide semantic security, reveals patterns in data

### Why These Limitations Exist

Apple's VNC Protocol 30 is required for compatibility with macOS Screen Sharing when:
- macOS 11-12 server communicates with OS X 10.11 or earlier clients
- Backward compatibility is needed with legacy systems

**Modern alternatives exist** (Protocol 33, 35, 36) but are not currently implemented.

### Security Recommendation

**🚫 DO NOT USE for:**
- Production environments with sensitive data
- Financial transactions
- Healthcare/PII data handling
- Any compliance-regulated environment (HIPAA, PCI-DSS, SOC 2, etc.)
- Untrusted networks

**✅ ACCEPTABLE USE:**
- Development and testing environments
- Controlled, isolated networks
- Automation of non-sensitive tasks
- Educational purposes

---

## 🔐 Credential Security

### Current Implementation Risks

1. **Environment Variable Exposure**
   - Credentials stored in `MACOS_PASSWORD` environment variable
   - Visible in process listings (`ps aux`, `/proc/[pid]/environ`)
   - Visible in Docker container inspection
   - May be logged by container orchestration systems

2. **No Encryption at Rest**
   - Passwords stored in plaintext in memory
   - No secure credential storage mechanism

3. **Network Transmission**
   - Passwords transmitted over network (even if "encrypted" with weak crypto)
   - Vulnerable to man-in-the-middle attacks on untrusted networks

### Mitigation Strategies

#### Immediate Actions

1. **Use Strong, Unique Passwords**
   ```bash
   # Generate a strong password
   openssl rand -base64 32
   ```

2. **Network Isolation**
   ```bash
   # Only allow connections from specific IPs
   sudo pfctl -e
   sudo pfctl -f /etc/pf.conf  # Configure firewall rules
   ```

3. **SSH Tunneling** (Recommended)
   ```bash
   # Create SSH tunnel for VNC
   ssh -L 5900:localhost:5900 user@remote-mac

   # Then connect to localhost:5900
   export MACOS_HOST=localhost
   export MACOS_PORT=5900
   ```

4. **Use Dedicated VNC-Only Account**
   - Create a limited macOS user specifically for VNC access
   - Restrict permissions to minimum required
   - Enable macOS Screen Recording permission ONLY for this user

#### Future Improvements (Planned)

- [ ] macOS Keychain integration for credential storage
- [ ] Support for certificate-based authentication
- [ ] Support for modern VNC protocols (33, 35, 36)
- [ ] Integration with secret management systems (HashiCorp Vault, AWS Secrets Manager)

---

## 🛡️ Network Security

### Required Security Measures

1. **Never Expose VNC to Public Internet**
   ```bash
   # BAD - Don't do this
   # Opening port 5900 to 0.0.0.0

   # GOOD - Firewall rules
   # Only allow from specific IP ranges
   ```

2. **Use VPN or Private Networks**
   - Deploy within VPC/VPN
   - Use Tailscale, WireGuard, or similar mesh VPN
   - Ensure end-to-end encrypted tunnels

3. **Monitor Access**
   - Enable macOS Screen Sharing logs
   - Monitor for unauthorized connection attempts
   - Set up alerts for failed authentication

### Network Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │────────>│  VPN/Tunnel  │────────>│  macOS VNC  │
│   (Docker)  │  TLS    │   (secure)   │  VNC    │   Server    │
└─────────────┘         └──────────────┘         └─────────────┘
```

---

## 🚨 Input Validation & Rate Limiting

### Protection Against Abuse

The application implements multiple security layers:

1. **Input Validation**
   - All text input limited to 10,000 characters
   - Coordinate values bounded to prevent integer overflow
   - Application identifiers restricted to safe character set
   - Validates all mouse button, delay, and dimension parameters

2. **Rate Limiting**
   - Default: 100 requests per 60 seconds per tool
   - Configurable via environment variables:
     ```bash
     export VNC_RATE_LIMIT_MAX=50       # Max calls per period
     export VNC_RATE_LIMIT_PERIOD=60    # Period in seconds
     ```

3. **Resource Management**
   - VNC connections properly closed via context managers
   - Socket timeouts prevent hanging connections
   - Thread-safe frame caching

---

## 📋 Security Checklist

### Before Deployment

- [ ] Review and acknowledge cryptographic limitations
- [ ] Assess data sensitivity and compliance requirements
- [ ] Set up network isolation (VPN, firewall, SSH tunnel)
- [ ] Create dedicated VNC-only macOS user account
- [ ] Configure strong, unique passwords
- [ ] Enable macOS Screen Sharing audit logging
- [ ] Set appropriate rate limits for your use case
- [ ] Configure logging level (INFO or WARNING for production)
- [ ] Document your security architecture
- [ ] Establish incident response procedures

### Production Hardening (If Applicable)

- [ ] Use SSH tunneling for all VNC connections
- [ ] Implement IP allowlisting
- [ ] Set up automated security scanning (bandit, safety)
- [ ] Enable comprehensive audit logging
- [ ] Implement monitoring and alerting
- [ ] Regular password rotation
- [ ] Dependency vulnerability scanning
- [ ] Network traffic encryption (VPN/TLS)
- [ ] Regular security assessments

### Docker Security

```json
{
  "mcpServers": {
    "remote-macos-use": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--security-opt", "no-new-privileges",
        "--cap-drop", "ALL",
        "--read-only",
        "--tmpfs", "/tmp",
        "-e", "MACOS_HOST=vpn.internal.host",
        "-e", "MACOS_USERNAME=vnc-user",
        "-e", "MACOS_PASSWORD_FILE=/run/secrets/vnc_password",
        "-e", "LOG_LEVEL=WARNING",
        "-e", "VNC_RATE_LIMIT_MAX=50",
        "--rm",
        "buryhuang/mcp-remote-macos-use:latest"
      ]
    }
  }
}
```

---

## 🐛 Reporting Security Vulnerabilities

### Responsible Disclosure

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email the maintainers privately with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fixes (if any)

3. Allow reasonable time for response (14 days)
4. Coordinate public disclosure timing

### Out of Scope

The following are **acknowledged limitations**, not vulnerabilities:
- Weak cryptography in VNC Protocol 30 (inherent protocol limitation)
- Credential exposure via environment variables (by design, documented)
- Lack of Protocol 33/35/36 support (roadmap item)

---

## 📚 Additional Resources

### Recommended Reading

- [Apple Remote Desktop Security](https://support.apple.com/guide/remote-desktop/encrypt-network-data-apdfe8e386b/mac)
- [VNC Protocol Specification](https://datatracker.ietf.org/doc/html/rfc6143)
- [Apple VNC Authentication Quirks](https://cafbit.com/post/apple_remote_desktop_quirks/)
- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)

### Alternative Solutions

For production environments requiring better security:

1. **Apple Remote Desktop** (ARD) - Modern protocols, better encryption
2. **TeamViewer** / **AnyDesk** - Commercial solutions with better security
3. **SSH + X11 Forwarding** - For command-line applications
4. **Mesh VPN Solutions** - Tailscale, Nebula, ZeroTier

---

## 📜 Security Version Support

| Version | Supported          | Security Updates |
| ------- | ------------------ | ---------------- |
| 0.1.x   | :white_check_mark: | Yes              |
| < 0.1   | :x:                | No               |

---

## ⚖️ Legal Disclaimer

**THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.**

Users are responsible for:
- Assessing security risks for their specific use case
- Implementing additional security measures as needed
- Compliance with all applicable laws and regulations
- Securing their own network and infrastructure

**The maintainers assume no liability for security breaches, data loss, or unauthorized access resulting from use of this software.**

---

*Last Updated: 2025-11-18*
*Security Policy Version: 1.0*
