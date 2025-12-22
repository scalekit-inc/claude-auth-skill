# Security Best Practices

## Overview

Security is critical when implementing authentication. This guide covers essential security practices for Scalekit authentication implementations.

## Environment & Secrets Management

### Never Commit Secrets

```bash
# ✅ Use .env file (add to .gitignore)
SCALEKIT_CLIENT_SECRET=your_secret_here

# ❌ NEVER commit secrets to version control
const secret = 'sktest_12345...';  // Don't do this!
```

### .gitignore Configuration

```
# Environment files
.env
.env.local
.env.production
.env.*.local

# Logs that might contain tokens
*.log
npm-debug.log*

# OS files
.DS_Store
Thumbs.db
```

### Use Environment-Specific Secrets

```javascript
// Development
SCALEKIT_CLIENT_SECRET=test_development_secret

// Staging
SCALEKIT_CLIENT_SECRET=test_staging_secret

// Production
SCALEKIT_CLIENT_SECRET=prod_live_secret
```

### Secrets Management Services

Use dedicated secret management for production:

**AWS Secrets Manager:**
```javascript
const AWS = require('aws-sdk');
const secretsManager = new AWS.SecretsManager();

const secret = await secretsManager.getSecretValue({
  SecretId: 'scalekit/production'
}).promise();

const credentials = JSON.parse(secret.SecretString);
```

**HashiCorp Vault:**
```javascript
const vault = require('node-vault')();

const { data } = await vault.read('secret/scalekit');
const clientSecret = data.client_secret;
```

## HTTPS & Transport Security

### Require HTTPS in Production

```javascript
// Redirect HTTP to HTTPS
app.use((req, res, next) => {
  if (req.header('x-forwarded-proto') !== 'https' && process.env.NODE_ENV === 'production') {
    return res.redirect(`https://${req.header('host')}${req.url}`);
  }
  next();
});
```

### Strict Transport Security (HSTS)

```javascript
import helmet from 'helmet';

app.use(helmet.hsts({
  maxAge: 31536000,  // 1 year
  includeSubDomains: true,
  preload: true
}));
```

### Certificate Validation

```javascript
// ✅ Default behavior - validates certificates
const scalekit = new Scalekit(envUrl, clientId, clientSecret);

// ❌ NEVER disable certificate validation
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';  // Don't do this!
```

## Cookie Security

### Production Cookie Settings

```javascript
const cookieConfig = {
  httpOnly: true,        // Prevents XSS attacks
  secure: true,          // HTTPS only
  sameSite: 'strict',    // CSRF protection
  path: '/',
  domain: process.env.COOKIE_DOMAIN,  // Explicit domain
  maxAge: expiresIn
};
```

### Cookie Signing (Optional Extra Layer)

```javascript
import cookieParser from 'cookie-parser';

// Sign cookies with secret
app.use(cookieParser(process.env.COOKIE_SECRET));

// Set signed cookie
res.cookie('accessToken', token, {
  ...cookieConfig,
  signed: true
});

// Read signed cookie
const token = req.signedCookies.accessToken;
```

### Avoid Session Fixation

```javascript
// Regenerate session ID after login
app.post('/auth/callback', async (req, res) => {
  // ... authenticate user ...

  // Clear any existing session
  req.session.destroy();

  // Create new session
  req.session.regenerate((err) => {
    if (err) return next(err);

    // Set new session data
    req.session.userId = user.sub;
    req.session.save();
  });
});
```

## CSRF Protection

### SameSite Cookie Attribute

```javascript
// Primary CSRF protection
const cookieConfig = {
  sameSite: 'strict'  // or 'lax' for better compatibility
};
```

### CSRF Tokens (Defense in Depth)

```javascript
import csrf from 'csurf';

// CSRF protection middleware
const csrfProtection = csrf({ cookie: true });

app.use(csrfProtection);

// Include token in forms
app.get('/login', (req, res) => {
  res.render('login', { csrfToken: req.csrfToken() });
});

// Validate on submission
app.post('/api/action', csrfProtection, (req, res) => {
  // CSRF token automatically validated
});
```

## XSS Prevention

### Content Security Policy (CSP)

```javascript
import helmet from 'helmet';

app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", "'unsafe-inline'"],  // Minimize inline scripts
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", "data:", "https:"],
    connectSrc: ["'self'", process.env.SCALEKIT_ENVIRONMENT_URL],
    fontSrc: ["'self'"],
    objectSrc: ["'none'"],
    mediaSrc: ["'self'"],
    frameSrc: ["'none'"]
  }
}));
```

### Input Sanitization

```javascript
import DOMPurify from 'isomorphic-dompurify';

// Sanitize user input before displaying
const sanitizedName = DOMPurify.sanitize(user.name);

// ❌ NEVER do this
res.send(`<h1>Welcome ${user.name}</h1>`);  // XSS vulnerable

// ✅ Use template engines with auto-escaping
res.render('welcome', { name: user.name });  // Escaped automatically
```

### HTTP-Only Cookies

```javascript
// ✅ Tokens not accessible to JavaScript
res.cookie('accessToken', token, {
  httpOnly: true  // Prevents document.cookie access
});

// ❌ Vulnerable to XSS
localStorage.setItem('accessToken', token);  // Avoid!
```

## SQL Injection Prevention

### Use Parameterized Queries

```javascript
// ✅ Parameterized query
const user = await db.query(
  'SELECT * FROM users WHERE email = $1',
  [email]
);

// ❌ String concatenation (SQL injection risk)
const user = await db.query(
  `SELECT * FROM users WHERE email = '${email}'`
);
```

### Use ORM/Query Builders

```javascript
// Using Prisma
const user = await prisma.user.findUnique({
  where: { email: email }
});

// Using Sequelize
const user = await User.findOne({
  where: { email: email }
});
```

## Rate Limiting

### Protect Authentication Endpoints

```javascript
import rateLimit from 'express-rate-limit';

// Login endpoint rate limiting
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 5,  // 5 attempts per window
  message: 'Too many login attempts, please try again later',
  standardHeaders: true,
  legacyHeaders: false,
});

app.get('/auth/login', loginLimiter, loginHandler);

// Stricter limit for token refresh
const refreshLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: 'Too many refresh attempts'
});

app.post('/auth/refresh', refreshLimiter, refreshHandler);
```

### IP-Based and User-Based Limits

```javascript
import RedisStore from 'rate-limit-redis';
import Redis from 'ioredis';

const redis = new Redis();

const limiter = rateLimit({
  store: new RedisStore({
    client: redis,
    prefix: 'rl:'
  }),
  windowMs: 15 * 60 * 1000,
  max: async (req) => {
    // Different limits for authenticated vs anonymous
    if (req.user) {
      return 100;  // Higher limit for authenticated users
    }
    return 20;  // Lower limit for anonymous
  },
  keyGenerator: (req) => {
    // Rate limit by user ID if authenticated, otherwise IP
    return req.user?.sub || req.ip;
  }
});
```

## Token Security

### Never Log Tokens

```javascript
// ❌ NEVER DO THIS
console.log('Access token:', accessToken);
logger.info({ token: accessToken });

// ✅ Log safe information only
console.log('User authenticated:', user.email);
logger.info({
  event: 'auth_success',
  userId: user.sub,
  email: user.email
});
```

### Token Validation

```javascript
// ✅ Always validate tokens server-side
async function authMiddleware(req, res, next) {
  const token = req.cookies.accessToken;

  try {
    const claims = await scalekit.validateToken(token, {
      issuer: process.env.SCALEKIT_ENVIRONMENT_URL || 'https://auth.scalekit.com',
      audience: process.env.SCALEKIT_CLIENT_ID
    });
    req.user = claims;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// ❌ NEVER trust client-provided data
const userId = req.headers['x-user-id'];  // Can be forged!
```

### Secure Token Storage

```javascript
// ✅ HttpOnly cookies
res.cookie('accessToken', token, {
  httpOnly: true,
  secure: true
});

// ❌ Local storage (vulnerable to XSS)
// Don't store tokens in localStorage or sessionStorage
```

## Callback URL Validation

### Strict URL Matching

```javascript
// Register exact callback URLs in Scalekit Dashboard
// ✅ https://app.example.com/auth/callback
// ❌ https://*.example.com/auth/callback (wildcard)

// Validate callback URL
const ALLOWED_CALLBACKS = [
  'https://app.example.com/auth/callback',
  'https://staging.example.com/auth/callback',
  'http://localhost:3000/auth/callback'  // Dev only
];

function getCallbackUrl(env) {
  const url = env === 'production'
    ? ALLOWED_CALLBACKS[0]
    : ALLOWED_CALLBACKS[2];

  if (!ALLOWED_CALLBACKS.includes(url)) {
    throw new Error('Invalid callback URL');
  }

  return url;
}
```

### Validate Redirect Parameters

```javascript
app.get('/auth/callback', async (req, res) => {
  const { code, error, state } = req.query;

  // Validate state parameter (CSRF protection)
  if (req.session.oauthState !== state) {
    return res.status(400).send('Invalid state parameter');
  }

  // ... continue with code exchange
});
```

## Error Handling

### Don't Leak Sensitive Information

```javascript
// ❌ Reveals internal details
app.use((err, req, res, next) => {
  res.status(500).json({ error: err.message, stack: err.stack });
});

// ✅ Generic error for clients, detailed logging server-side
app.use((err, req, res, next) => {
  logger.error('Authentication error', {
    error: err.message,
    stack: err.stack,
    userId: req.user?.sub,
    ip: req.ip
  });

  res.status(500).json({
    error: 'Authentication failed',
    // Only include details in development
    ...(process.env.NODE_ENV === 'development' && { details: err.message })
  });
});
```

### Consistent Error Messages

```javascript
// ❌ Different messages reveal information
if (!userExists) {
  return res.status(401).send('User not found');
}
if (!passwordValid) {
  return res.status(401).send('Invalid password');
}

// ✅ Same message for all auth failures
if (!userExists || !passwordValid) {
  return res.status(401).send('Invalid credentials');
}
```

## Monitoring & Logging

### Security Event Logging

```javascript
const securityLogger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'security.log' })
  ]
});

// Log authentication events
function logAuthEvent(event, details) {
  securityLogger.info(event, {
    timestamp: new Date().toISOString(),
    ip: details.ip,
    userAgent: details.userAgent,
    userId: details.userId,
    success: details.success,
    ...details
  });
}

// Usage
app.post('/auth/callback', async (req, res) => {
  try {
    const result = await scalekit.authenticateWithCode(code, callbackUrl);

    logAuthEvent('auth_success', {
      userId: result.user.sub,
      email: result.user.email,
      ip: req.ip,
      userAgent: req.get('user-agent'),
      success: true
    });

  } catch (error) {
    logAuthEvent('auth_failure', {
      ip: req.ip,
      userAgent: req.get('user-agent'),
      success: false,
      error: error.message
    });
  }
});
```

### Anomaly Detection

```javascript
async function detectAnomalies(userId) {
  const recentLogins = await getRecentLogins(userId, 24); // Last 24 hours

  // Multiple logins from different locations
  const uniqueIPs = new Set(recentLogins.map(l => l.ip)).size;
  if (uniqueIPs > 5) {
    await alertSecurityTeam({
      userId,
      alert: 'Multiple IPs detected',
      count: uniqueIPs
    });
  }

  // Rapid login attempts
  if (recentLogins.length > 50) {
    await alertSecurityTeam({
      userId,
      alert: 'Excessive login attempts',
      count: recentLogins.length
    });
  }
}
```

## Dependency Security

### Regular Updates

```bash
# Check for vulnerabilities
npm audit

# Fix automatically
npm audit fix

# Update dependencies
npm update
```

### Use Lock Files

```bash
# Ensure consistent dependency versions
npm ci  # Instead of npm install in production
```

### Automated Scanning

```yaml
# GitHub Actions security scan
name: Security Scan
on: [push]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

## Production Checklist

- [ ] All secrets in environment variables, not code
- [ ] HTTPS enabled with valid certificate
- [ ] HSTS header configured
- [ ] Cookie settings: httpOnly, secure, sameSite
- [ ] Content Security Policy (CSP) configured
- [ ] CSRF protection enabled
- [ ] Input validation and sanitization
- [ ] Rate limiting on auth endpoints
- [ ] Error messages don't leak information
- [ ] Security event logging enabled
- [ ] Callback URLs strictly validated
- [ ] Token validation on every request
- [ ] Regular dependency updates
- [ ] Vulnerability scanning automated
- [ ] Monitoring and alerting configured

## Incident Response

### Compromised Secrets

If credentials are compromised:

1. **Immediately** rotate credentials in Scalekit Dashboard
2. Update environment variables with new credentials
3. Deploy updated configuration
4. Invalidate all active sessions
5. Force all users to re-authenticate
6. Review security logs for suspicious activity
7. Notify affected users if necessary

### Suspicious Activity

```javascript
async function handleSuspiciousActivity(userId) {
  // Lock account
  await db.users.update(userId, { locked: true });

  // Invalidate all sessions
  await db.sessions.deleteMany({ userId });

  // Notify user
  await sendEmail(user.email, {
    subject: 'Security Alert',
    body: 'Suspicious activity detected...'
  });

  // Alert security team
  await notifySecurityTeam({
    userId,
    reason: 'Suspicious activity detected'
  });
}
```

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [Scalekit Security Documentation](https://docs.scalekit.com/security)

## Next Steps

- Review [session-management.md](session-management.md)
- Implement security monitoring
- Set up automated vulnerability scanning
- Configure security headers
- Enable audit logging
