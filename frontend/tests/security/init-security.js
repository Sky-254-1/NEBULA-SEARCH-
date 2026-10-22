init.js
mkdir -p tests/security
cd tests/security
echo '{
  "version": "1.0.0",
  "description": "Security hardening for Vitest environment",
  "scripts": {
    "security:setup": "node ../init-security.js",
    "security:clean": "rm -f security-logs.json"
  }
}' > package.json
echo 'const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

class SecurityManager {
  constructor() {
    this.securityLogs = [];
    this.allowedPaths = [
      process.cwd(),
      path.join(process.cwd(), "frontend/src"),
      path.join(process.cwd(), "frontend/tests"),
      path.join(process.cwd(), "node_modules/.vite"),
    ];
    this.blockedPatterns = [
      /\\.env\\./,
      /\\.key$/,
      /\\.pem$/,
      /\\.p12$/,
      /\\.crt$/,
      /\\\\.aws\\//,
      /\\\\.ssh\\//,
      /\\/etc\\//,
      /C:\\\\Windows\\\\,\n      /proc\\//,
      /\\/var\\//,
    ];
    this.securityEnabled = true;
  }

  logSecurityEvent(event, details) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      event,
      details,
      severity: this.getSeverity(event),
    };
    this.securityLogs.push(logEntry);
    
    if (this.securityLogs.length > 1000) {
      this.securityLogs = this.securityLogs.slice(-1000);
    }
    
    if (event.includes("BLOCK") || event.includes("ERROR")) {
      console.error(`[SECURITY] ${event}`, details);
    } else {
      console.log(`[SECURITY] ${event}`, details);
    }
  }

  getSeverity(event) {
    if (event.includes("CRITICAL") || event.includes("BLOCK")) return "CRITICAL";
    if (event.includes("ERROR") || event.includes("FORBIDDEN")) return "HIGH";
    if (event.includes("WARN") || event.includes("DENIED")) return "MEDIUM";
    return "LOW";
  }

  checkPathAccess(filePath, context = "unknown") {
    try {
      const resolvedPath = path.resolve(filePath);
      
      // Check against allowed paths
      const isAllowed = this.allowedPaths.some((allowedPath) =>
        resolvedPath === allowedPath || resolvedPath.startsWith(allowedPath + path.sep)
      );
      
      if (!isAllowed) {
        // Check against blocked patterns
        const isBlocked = this.blockedPatterns.some((pattern) =>
          pattern.test(resolvedPath) || pattern.test(filePath)
        );
        
        if (isBlocked) {
          this.logSecurityEvent(
            "PATH_ACCESS_BLOCKED",
            `Path '${filePath}' (resolved: '${resolvedPath}') blocked for context: ${context}`
          );
          return false;
        }
        
        // Log warning for paths not explicitly allowed
        this.logSecurityEvent(
          "PATH_ACCESS_WARNING",
          `Path '${filePath}' (resolved: '${resolvedPath}') not in allowed paths for context: ${context}`
        );
        
        // Deny access by default for security
        return false;
      }
      
      return true;
    } catch (error) {
      this.logSecurityEvent(
        "PATH_ACCESS_ERROR",
        `Error checking path '${filePath}': ${error.message}`
      );
      return false;
    }
  }

  checkEnvironmentVariable(varName, value) {
    const sensitivePatterns = [
      /API_KEY/i,
      /SECRET/i,
      /PASSWORD/i,
      /TOKEN/i,
      /PRIVATE_KEY/i,
      /ACCESS_KEY/i,
      /JWT/i,
      /AUTH/i,
      /CERTIFICATE/i,
    ];
    
    if (sensitivePatterns.some((pattern) => pattern.test(varName))) {
      this.logSecurityEvent(
        "SENSITIVE_ENV_VAR_ACCESS",
        `Attempt to access sensitive environment variable: ${varName}`
      );
      return false;
    }
    
    return true;
  }

  validateNetworkRequest(url, requestType = "fetch") {
    try {
      const urlObj = new URL(url);
      
      // Block requests to internal network
      const internalHostnames = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '169.254.',
        '192.168.',
        '10.',
        '172.16.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
      ];
      
      // Block requests to internal TLDs
      const internalTlds = [
        '.internal',
        '.local',
        '.localhost',
      ];
      
      const hostname = urlObj.hostname;
      const hostnameParts = hostname.split('.');
      
      // Check against internal IPs
      const isInternalIP = internalHostnames.some((internalPattern) =>
        hostname.startsWith(internalPattern)
      );
      
      // Check against internal TLDs
      const isInternalTLD = internalTlds.some((internalTLD) =>
        hostname.endsWith(internalTLD)
      );
      
      // Check for reserved port ranges
      const port = urlObj.port || (urlObj.protocol === 'https:' ? '443' : '80');
      const portNum = parseInt(port, 10);
      
      const reservedPorts = [
        22,  // SSH
        23,  // Telnet
        25,  // SMTP
        53,  // DNS
        110, // POP3
        135, // MS Exchange
        139, // NetBIOS
        143, // IMAP
        3306, // MySQL
        3389, // RDP
        5432, // PostgreSQL
        6379, // Redis
        8080, // Alternative HTTP
        8443, // Alternative HTTPS
      ];
      
      if (isInternalIP || isInternalTLD || reservedPorts.includes(portNum)) {
        this.logSecurityEvent(
          "NETWORK_REQUEST_BLOCKED",
          `Network request to internal resource: ${url} blocked"
        );
        return false;
      }
      
      return true;
    } catch (error) {
      this.logSecurityEvent(
        "NETWORK_REQUEST_ERROR",
        `Error validating network request '${url}': ${error.message}`
      );
      return false;
    }
  }

  generateSecurityReport() {
    const report = {
      timestamp: new Date().toISOString(),
      totalEvents: this.securityLogs.length,
      eventsBySeverity: this.securityLogs.reduce((acc, log) => {
        acc[log.severity] = (acc[log.severity] || 0) + 1;
        return acc;
      }, {}),
      recentEvents: this.securityLogs.slice(-100),
      securityEnabled: this.securityEnabled,
    };
    
    // Save report
    const reportPath = path.join(process.cwd(), 'tests', 'security', 'security-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    return report;
  }
}

const securityManager = new SecurityManager();

// Global security validation
if (typeof window !== 'undefined') {
  // Override fetch to add security validation
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const [resource, config] = args;
    let url = typeof resource === 'string' ? resource : resource.url;
    
    if (!securityManager.validateNetworkRequest(url, 'fetch')) {
      throw new Error(`Security: Network request blocked to ${url}`);
    }
    
    return originalFetch.apply(this, args);
  };

  // Override XMLHttpRequest
  const OriginalXMLHttpRequest = window.XMLHttpRequest;
  window.XMLHttpRequest = function() {
    const xhr = new OriginalXMLHttpRequest();
    
    const originalOpen = xhr.open;
    xhr.open = function(method, url, ...args) {
      if (!securityManager.validateNetworkRequest(url, 'xhr')) {
        throw new Error(`Security: XMLHttpRequest blocked to ${url}`);
      }
      
      return originalOpen.apply(this, arguments);
    };
    
    return xhr;
  };

  // Override WebSocket
  const originalWebSocket = window.WebSocket;
  window.WebSocket = function(url) {
    if (!securityManager.validateNetworkRequest(url, 'websocket')) {
      throw new Error(`Security: WebSocket connection blocked to ${url}`);
    }
    
    return new originalWebSocket(url);
  };

  // Block file system access
  Object.defineProperty(window, 'showOpenFilePicker', {
    value: (...args) => {
      throw new Error('Security: File picker access blocked');
    },
    configurable: true,
  });

  Object.defineProperty(window, 'fileSystem', {
    value: null,
    configurable: true,
  });

  // Block sensitive environment variable access
  Object.defineProperty(window, 'process', {
    value: {
      ...process,
      env: new Proxy(process.env, {
        get: (target, prop) => {
          if (securityManager.checkEnvironmentVariable(prop, target[prop])) {
            return target[prop];
          }
          return undefined;
        },
      }),
    },
    configurable: true,
  });

  // Block import of sensitive modules
  const originalImport = window.import;
  window.import = async (module) => {
    if (securityManager.checkPathAccess(module, 'dynamic_import')) {
      return originalImport.apply(this, arguments);
    }
    throw new Error(`Security: Dynamic import blocked for module: ${module}`);
  };

  // Security event handler
  window.addEventListener('error', (event) => {
    if (event.error && event.error.message.includes('Security:')) {
      securityManager.logSecurityEvent(
        'SECURITY_ERROR',
        `Security-related error: ${event.error.message}`
      );
    }
  });

  // Generate initial security report
  if (!fs.existsSync(path.join(process.cwd(), 'tests', 'security', 'security-report.json'))) {
    securityManager.generateSecurityReport();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = securityManager;
}

console.log('🛡️  Security manager initialized successfully');
