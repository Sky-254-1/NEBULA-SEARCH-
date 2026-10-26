#!/usr/bin/env python3
"""
Secret Scanning Script for CI Security Checks

Scans for:
- .env files in git history
- Exposed secrets in current codebase
- Common secret patterns (API keys, passwords, tokens)
- Potentially sensitive configuration patterns
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional


# Patterns for common secret types
SECRET_PATTERNS = {
    # API Keys
    "api_key": re.compile(r'[A-Za-z0-9_\-]{20,}', re.IGNORECASE),
    "aws_access_key": re.compile(r'AKIA[0-9A-Z]{16}'),
    "aws_secret_key": re.compile(r'[A-Za-z0-9/+=]{40}'),
    
    # Passwords and Credentials
    "password": re.compile(r'(?:password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
    "credential": re.compile(r'(?:credential|cred)\s*[=:]\s*["\']?([^"\'\s]+)["\']?', re.IGNORECASE),
    
    # Tokens
    "jwt_secret": re.compile(r'(?i)jwt[_\s]?(?:secret|key)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'),
    "session_secret": re.compile(r'(?i)session[_\s]?(?:secret|key)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'),
    "encryption_key": re.compile(r'(?i)encryption[_\s]?(?:key|secret)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'),
    "token": re.compile(r'(?i)token\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?'),
    
    # Database Credentials
    "database_password": re.compile(r'(?i)(?:database|db|postgres|mysql|mongodb).{0,20}(?:password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]+)["\']?'),
    "connection_string": re.compile(r'(?:postgresql|mysql|mongodb|redis)://[^:]+:[^@]+@[^\s]+'),
    
    # Cloud Provider Keys
    "openai_api_key": re.compile(r'(?i)sk-[a-zA-Z0-9]{20,}'),
    "stripe_api_key": re.compile(r'(?i)(?:sk|pk)_(?:test|live)_[a-zA-Z0-9]{20,}'),
    "sendgrid_api_key": re.compile(r'(?i)SG\.[a-zA-Z0-9_\-]{22,}\.[a-zA-Z0-9_\-]{22,}'),
    "github_token": re.compile(r'(?i)gh[pous]_[A-Za-z0-9_]{36,}'),
    
    # Generic Secrets
    "secret_key": re.compile(r'(?i)secret[_\s]?(?:key|value)?\s*[=:]\s*["\']?([A-Za-z0-9_\-]{16,})["\']?'),
    "private_key": re.compile(r'-----BEGIN(?: RSA| EC| DSA| OpenSSH)? PRIVATE KEY-----'),
}

# Known safe patterns to exclude
SAFE_PATTERNS = {
    "placeholder": re.compile(r'(?:change[-_]?me|placeholder|example|your[_-]here|replace[-_]me|insert[_-]value|xxx+|#+)', re.IGNORECASE),
    "test_pattern": re.compile(r'(?:test|dummy|fake|sample|dev|dev[_-]?only)', re.IGNORECASE),
    "commented": re.compile(r'^\s*#.*$'),
    "env_example": re.compile(r'\.example$'),
}

# Files and directories to exclude from scanning
EXCLUDE_PATHS = {
    'node_modules',
    '.git',
    '__pycache__',
    'venv',
    '.venv',
    'env',
    '.env',
    'dist',
    'build',
    'coverage',
    '.coverage',
    '.pytest_cache',
    '.mypy_cache',
    'htmlcov',
    '.tox',
    'logs',
}


def should_exclude(path: str, exclude_patterns: set = None) -> bool:
    """Check if a path should be excluded from scanning."""
    if exclude_patterns is None:
        exclude_patterns = EXCLUDE_PATHS
    
    path_parts = set(Path(path).parts)
    return bool(path_parts & exclude_patterns)


def is_safe_value(value: str) -> bool:
    """Check if a value appears to be a safe placeholder."""
    for pattern in SAFE_PATTERNS.values():
        if pattern.search(value):
            return True
    return False


def scan_file_for_secrets(filepath: str, base_dir: str) -> List[Dict[str, Any]]:
    """Scan a single file for potential secrets."""
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        return findings
    
    for line_num, line in enumerate(lines, 1):
        # Skip commented lines
        if line.strip().startswith('#'):
            continue
        
        for pattern_name, pattern in SECRET_PATTERNS.items():
            matches = pattern.finditer(line)
            for match in matches:
                found_value = match.group(0)
                
                # Check if it's a safe placeholder
                if is_safe_value(found_value):
                    continue
                
                findings.append({
                    'file': os.path.relpath(filepath, base_dir),
                    'line': line_num,
                    'pattern': pattern_name,
                    'match': found_value[:50] + '...' if len(found_value) > 50 else found_value,
                    'severity': 'HIGH' if 'password' in pattern_name or 'secret' in pattern_name or 'private_key' in pattern_name else 'MEDIUM',
                    'description': f'Potential {pattern_name.replace("_", " ")} detected',
                })
    
    return findings


def scan_directory(base_dir: str) -> List[Dict[str, Any]]:
    """Scan all Python and config files in a directory."""
    all_findings = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(d)]
        
        for file in files:
            filepath = os.path.join(root, file)
            
            # Skip binary files and excluded paths
            if should_exclude(filepath):
                continue
            
            # Only scan text files we care about
            ext = os.path.splitext(file)[1].lower()
            if ext not in {'.py', '.yml', '.yaml', '.json', '.env', '.txt', '.cfg', '.ini', '.toml'}:
                continue
            
            findings = scan_file_for_secrets(filepath, base_dir)
            all_findings.extend(findings)
    
    return all_findings


def check_git_history(base_dir: str) -> List[Dict[str, Any]]:
    """Check git history for sensitive files like .env.development, .env.production."""
    findings = []
    
    sensitive_files = ['.env.development', '.env.production', '.env', 'secrets.yaml', 'secret.yaml']
    
    try:
        # Check for sensitive files in recent commits
        for sensitive_file in sensitive_files:
            result = subprocess.run(
                ['git', 'log', '--oneline', '--follow', '--', sensitive_file],
                cwd=base_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    findings.append({
                        'type': 'git_history',
                        'severity': 'CRITICAL',
                        'file': sensitive_file,
                        'commit_count': len(lines),
                        'description': f'File "{sensitive_file}" found in git history ({len(lines)} commits)',
                        'remediation': f'1. Remove from history: git filter-branch --force --index-filter "git rm --cached --ignore-unmatch {sensitive_file}" --prune-empty HEAD\n'
                                      f'2. Force push: git push origin --force --all\n'
                                      f'3. Rotate all credentials that may have been exposed',
                    })
    except subprocess.TimeoutExpired:
        findings.append({
            'type': 'git_history',
            'severity': 'WARNING',
            'file': 'git_history_check',
            'description': 'Git history check timed out',
            'remediation': 'Manual review of git history recommended',
        })
    except Exception as e:
        findings.append({
            'type': 'git_history',
            'severity': 'WARNING',
            'file': 'git_history_check',
            'description': f'Could not check git history: {str(e)}',
            'remediation': 'Manual review of git history recommended',
        })
    
    return findings


def check_working_tree_for_env(base_dir: str) -> List[Dict[str, Any]]:
    """Check if .env files exist in the working tree."""
    findings = []
    
    sensitive_files = ['.env.development', '.env.production', '.env']
    
    for sensitive_file in sensitive_files:
        filepath = os.path.join(base_dir, sensitive_file)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            # Check if it's actually tracked or if it's a real file with potential secrets
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check if it contains actual secrets or placeholders
                has_real_secrets = False
                for pattern_name, pattern in SECRET_PATTERNS.items():
                    matches = pattern.findall(content)
                    for match in matches:
                        if not is_safe_value(match):
                            has_real_secrets = True
                            break
                    if has_real_secrets:
                        break
                
                severity = 'CRITICAL' if has_real_secrets else 'WARNING'
                
                findings.append({
                    'type': 'working_tree',
                    'severity': severity,
                    'file': sensitive_file,
                    'description': f'File "{sensitive_file}" exists in working tree',
                    'remediation': f'Add "{sensitive_file}" to .gitignore and never commit it',
                })
            except Exception:
                findings.append({
                    'type': 'working_tree',
                    'severity': 'WARNING',
                    'file': sensitive_file,
                    'description': f'File "{sensitive_file}" exists but could not be read',
                    'remediation': f'Add "{sensitive_file}" to .gitignore',
                })
    
    return findings


def check_gitignore_rules(base_dir: str) -> List[Dict[str, Any]]:
    """Check if .env files are properly ignored in .gitignore."""
    findings = []
    gitignore_path = os.path.join(base_dir, '.gitignore')
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        env_patterns = ['.env', '.env.*', '.env.development', '.env.production']
        missing_patterns = []
        
        for pattern in env_patterns:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            findings.append({
                'type': 'gitignore',
                'severity': 'MEDIUM',
                'description': f'Missing .gitignore patterns: {", ".join(missing_patterns)}',
                'remediation': f'Add these patterns to .gitignore:\n' + '\n'.join(f'  {p}' for p in missing_patterns),
            })
    else:
        findings.append({
            'type': 'gitignore',
            'severity': 'HIGH',
            'description': 'No .gitignore file found',
            'remediation': 'Create .gitignore and add environment file patterns',
        })
    
    return findings


def check_for_trufflehog() -> Tuple[bool, Optional[str]]:
    """Check if truffleHog is available."""
    try:
        result = subprocess.run(['trufflehog', '--version'], 
                              capture_output=True, timeout=10)
        if result.returncode == 0:
            return True, result.stdout.decode()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False, None


def check_for_git_secrets() -> Tuple[bool, Optional[str]]:
    """Check if git-secrets is available."""
    try:
        result = subprocess.run(['git-secrets', '--version'], 
                              capture_output=True, timeout=10)
        if result.returncode == 0:
            return True, result.stdout.decode()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False, None


def run_trufflehog(base_dir: str) -> List[Dict[str, Any]]:
    """Run truffleHog if available."""
    findings = []
    available, version = check_for_trufflehog()
    
    if not available:
        return findings
    
    try:
        result = subprocess.run(
            ['trufflehog', 'filesystem', '.', '--json'],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        finding = json.loads(line)
                        findings.append({
                            'type': 'trufflehog',
                            'severity': 'HIGH',
                            'file': finding.get('SourceMetadata', {}).get('Data', {}).get('File', 'unknown'),
                            'description': finding.get('Raw', 'Secret detected'),
                            'remediation': 'Review and remove exposed secrets, then rotate credentials',
                        })
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        findings.append({
            'type': 'trufflehog',
            'severity': 'WARNING',
            'description': f'TruffleHog execution error: {str(e)}',
        })
    
    return findings


def run_git_secrets(base_dir: str) -> List[Dict[str, Any]]:
    """Run git-secrets if available."""
    findings = []
    available, version = check_for_git_secrets()
    
    if not available:
        return findings
    
    try:
        # Scan current directory
        result = subprocess.run(
            ['git-secrets', '--scan'],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line and 'found' in line.lower():
                    findings.append({
                        'type': 'git_secrets',
                        'severity': 'HIGH',
                        'description': line.strip(),
                        'remediation': 'Review and remove exposed secrets',
                    })
    except Exception as e:
        findings.append({
            'type': 'git_secrets',
            'severity': 'WARNING',
            'description': f'Git-secrets execution error: {str(e)}',
        })
    
    return findings


def generate_report(all_findings: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
    """Generate a detailed JSON report."""
    # Categorize findings
    critical = [f for f in all_findings if f.get('severity') == 'CRITICAL']
    high = [f for f in all_findings if f.get('severity') == 'HIGH']
    medium = [f for f in all_findings if f.get('severity') == 'MEDIUM']
    warning = [f for f in all_findings if f.get('severity') == 'WARNING']
    
    # Summary
    report = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'summary': {
            'total_findings': len(all_findings),
            'critical': len(critical),
            'high': len(high),
            'medium': len(medium),
            'warning': len(warning),
            'trufflehog_available': check_for_trufflehog()[0],
            'git_secrets_available': check_for_git_secrets()[0],
        },
        'findings': all_findings,
        'recommendations': [
            'Rotate all exposed credentials immediately',
            'Remove sensitive files from git history using git filter-branch',
            'Force push the cleaned history to remove secrets from remote',
            'Add environment files to .gitignore',
            'Use environment-specific .env.example templates instead of real files',
            'Consider using a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)',
            'Enable branch protection to prevent accidental secret commits',
        ],
    }
    
    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report


def main():
    """Main entry point."""
    base_dir = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
    output_dir = os.environ.get('GITHUB_WORKSPACE', os.getcwd())
    report_path = os.path.join(output_dir, 'security-scan-report.json')
    
    print("=" * 60)
    print("Secret Scanning Report")
    print("=" * 60)
    
    all_findings = []
    
    # Check working tree for .env files
    print("\n[1/6] Checking working tree for .env files...")
    env_findings = check_working_tree_for_env(base_dir)
    all_findings.extend(env_findings)
    for f in env_findings:
        print(f"  {f['severity']}: {f['description']}")
    
    # Check gitignore rules
    print("\n[2/6] Checking .gitignore configuration...")
    gitignore_findings = check_gitignore_rules(base_dir)
    all_findings.extend(gitignore_findings)
    for f in gitignore_findings:
        print(f"  {f['severity']}: {f['description']}")
    
    # Check git history
    print("\n[3/6] Checking git history for sensitive files...")
    history_findings = check_git_history(base_dir)
    all_findings.extend(history_findings)
    for f in history_findings:
        print(f"  {f['severity']}: {f['description']}")
    
    # Scan current files
    print("\n[4/6] Scanning files for secret patterns...")
    file_findings = scan_directory(base_dir)
    all_findings.extend(file_findings)
    print(f"  Found {len(file_findings)} potential secret patterns")
    
    # Run truffleHog if available
    print("\n[5/6] Checking for truffleHog availability...")
    trufflehog_findings = run_trufflehog(base_dir)
    all_findings.extend(trufflehog_findings)
    if trufflehog_findings:
        print(f"  TruffleHog found {len(trufflehog_findings)} issues")
    else:
        print("  TruffleHog not available, using built-in scanner")
    
    # Run git-secrets if available
    print("\n[6/6] Checking for git-secrets availability...")
    git_secrets_findings = run_git_secrets(base_dir)
    all_findings.extend(git_secrets_findings)
    if git_secrets_findings:
        print(f"  Git-secrets found {len(git_secrets_findings)} issues")
    
    # Generate report
    print("\n" + "=" * 60)
    print("Generating report...")
    report = generate_report(all_findings, report_path)
    
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total findings: {report['summary']['total_findings']}")
    print(f"  Critical: {report['summary']['critical']}")
    print(f"  High: {report['summary']['high']}")
    print(f"  Medium: {report['summary']['medium']}")
    print(f"  Warning: {report['summary']['warning']}")
    print(f"\nReport saved to: {report_path}")
    
    # Determine exit code
    if report['summary']['critical'] > 0 or report['summary']['high'] > 0:
        print("\n[!] CRITICAL OR HIGH SEVERITY ISSUES DETECTED")
        print("\nRemediation steps:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
        print("\nThis workflow should fail. Review the report and remediate.")
        return 1
    elif report['summary']['warning'] > 0 or report['summary']['medium'] > 0:
        print("\n[!] WARNINGS OR MEDIUM SEVERITY ISSUES DETECTED")
        print("Review the report and consider remediation.")
        return 0
    else:
        print("\n[✓] No critical issues detected")
        print("Security scan completed successfully.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
