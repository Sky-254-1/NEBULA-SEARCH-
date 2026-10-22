"""Tests for app/services/mfa.py — TOTP/2FA secret generation, verification, backup codes."""

import time
import hashlib
import hmac
from io import BytesIO

import pytest
import pyotp

from app.services.mfa import MFAService, enroll_mfa, verify_mfa_token, MFAEnrollment


class TestMFAService:
    """Tests for MFAService — TOTP and backup code operations."""

    # ── Secret Generation ──────────────────────────────────────────────

    def test_generate_secret_returns_string(self):
        """Primary success: generate_secret returns a non-empty string."""
        secret = MFAService.generate_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0

    def test_generate_secret_is_base32(self):
        """Generated secret is valid base32 (pyotp-compatible)."""
        secret = MFAService.generate_secret()
        # pyotp will raise if invalid — this is the validation
        totp = pyotp.TOTP(secret)
        assert totp.now() is not None

    def test_generate_secret_unique(self):
        """Two calls produce different secrets."""
        s1 = MFAService.generate_secret()
        s2 = MFAService.generate_secret()
        assert s1 != s2

    # ── TOTP URI ──────────────────────────────────────────────────────

    def test_get_totp_uri_contains_email(self):
        """TOTP URI includes the user email (URL-encoded)."""
        secret = MFAService.generate_secret()
        uri = MFAService.get_totp_uri(secret, "user@example.com")
        assert "user%40example.com" in uri or "user@example.com" in uri

    def test_get_totp_uri_starts_with_otpauth(self):
        """TOTP URI has correct scheme."""
        uri = MFAService.get_totp_uri("secret", "test@example.com")
        assert uri.startswith("otpauth://totp/")

    # ── QR Code ───────────────────────────────────────────────────────

    def test_generate_qr_code_returns_bytes(self):
        """QR code generation returns PNG bytes."""
        uri = "otpauth://totp/test?secret=1234&issuer=Nebula"
        qr_bytes = MFAService.generate_qr_code(uri)
        assert isinstance(qr_bytes, bytes)
        assert len(qr_bytes) > 0

    def test_generate_qr_code_png_header(self):
        """QR code bytes contain PNG magic bytes."""
        uri = "otpauth://totp/test?secret=1234&issuer=Nebula"
        qr_bytes = MFAService.generate_qr_code(uri)
        assert qr_bytes.startswith(b'\x89PNG')

    # ── Token Verification ────────────────────────────────────────────

    def test_verify_token_valid(self):
        """Primary success: valid TOTP token returns True."""
        secret = MFAService.generate_secret()
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        assert MFAService.verify_token(secret, valid_token) is True

    def test_verify_token_invalid(self):
        """Failure path: invalid token returns False."""
        secret = MFAService.generate_secret()
        assert MFAService.verify_token(secret, "000000") is False

    def test_verify_token_expired(self):
        """Failure path: expired token (outside window) returns False."""
        secret = MFAService.generate_secret()
        totp = pyotp.TOTP(secret)
        # Generate a token from the past (previous 30s window, outside default window=1)
        old_time = int(time.time()) - 90  # 3 windows ago
        expired_token = totp.at(old_time)
        assert MFAService.verify_token(secret, expired_token) is False

    def test_verify_token_empty(self):
        """Failure path: empty token returns False."""
        secret = MFAService.generate_secret()
        assert MFAService.verify_token(secret, "") is False

    # ── Backup Codes ──────────────────────────────────────────────────

    def test_generate_backup_codes_default_count(self):
        """Default backup code generation produces 10 codes."""
        codes = MFAService.generate_backup_codes()
        assert len(codes) == 10

    def test_generate_backup_codes_custom_count(self):
        """Custom count produces requested number of codes."""
        codes = MFAService.generate_backup_codes(count=5)
        assert len(codes) == 5

    def test_generate_backup_codes_format(self):
        """Each backup code has format XXXX-XXXX."""
        codes = MFAService.generate_backup_codes(count=3)
        for code in codes:
            assert len(code) == 9  # 4 chars + dash + 4 chars
            assert code[4] == '-'
            parts = code.split('-')
            assert len(parts) == 2
            assert len(parts[0]) == 4
            assert len(parts[1]) == 4

    def test_generate_backup_codes_uppercase_hex(self):
        """Backup codes contain only uppercase hex chars."""
        codes = MFAService.generate_backup_codes(count=3)
        for code in codes:
            hex_part = code.replace('-', '')
            assert all(c in '0123456789ABCDEF' for c in hex_part)

    def test_generate_backup_codes_unique(self):
        """Generated codes are unique."""
        codes = MFAService.generate_backup_codes(count=10)
        assert len(set(codes)) == 10

    # ── Backup Code Hashing ───────────────────────────────────────────

    def test_hash_backup_code(self):
        """hash_backup_code produces deterministic SHA-256 hash."""
        code = "ABCD-1234"
        h1 = MFAService.hash_backup_code(code)
        h2 = MFAService.hash_backup_code(code)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_hash_backup_code_normalizes(self):
        """hash_backup_code normalizes dashes and case."""
        h1 = MFAService.hash_backup_code("ABCD-1234")
        h2 = MFAService.hash_backup_code("abcd-1234")
        h3 = MFAService.hash_backup_code("ABCD1234")
        assert h1 == h2 == h3

    # ── Backup Code Verification ─────────────────────────────────────

    def test_verify_backup_code_valid(self):
        """Primary success: valid backup code matches stored hash."""
        code = "ABCD-1234"
        stored_hash = MFAService.hash_backup_code(code)
        assert MFAService.verify_backup_code(code, stored_hash) is True

    def test_verify_backup_code_invalid(self):
        """Failure path: wrong code doesn't match hash."""
        stored_hash = MFAService.hash_backup_code("ABCD-1234")
        assert MFAService.verify_backup_code("DCBA-4321", stored_hash) is False

    def test_verify_backup_code_tampered(self):
        """Failure path: tampered hash comparison."""
        stored_hash = "a" * 64  # fake hash
        assert MFAService.verify_backup_code("ABCD-1234", stored_hash) is False

    # ── verify_mfa_token function ─────────────────────────────────────

    def test_verify_mfa_token_valid_totp(self):
        """verify_mfa_token with valid TOTP returns (True, '')."""
        secret = MFAService.generate_secret()
        totp = pyotp.TOTP(secret)
        token = totp.now()
        is_valid, error = verify_mfa_token(secret, token)
        assert is_valid is True
        assert error == ""

    def test_verify_mfa_token_invalid_totp(self):
        """verify_mfa_token with invalid TOTP returns (False, error)."""
        secret = MFAService.generate_secret()
        is_valid, error = verify_mfa_token(secret, "000000")
        assert is_valid is False
        assert "Invalid" in error or len(error) > 0

    def test_verify_mfa_token_bad_format(self):
        """verify_mfa_token with non-6-digit returns (False, format error)."""
        secret = MFAService.generate_secret()
        is_valid, error = verify_mfa_token(secret, "abc")
        assert is_valid is False

    def test_verify_mfa_token_backup_code_format(self):
        """verify_mfa_token with 8-char input says to use backup endpoint."""
        secret = MFAService.generate_secret()
        is_valid, error = verify_mfa_token(secret, "ABCD1234")
        assert is_valid is False
        assert "backup code" in error.lower()

    def test_verify_mfa_token_strips_dashes_and_spaces(self):
        """verify_mfa_token normalizes input before checking."""
        secret = MFAService.generate_secret()
        totp = pyotp.TOTP(secret)
        token = totp.now()
        # Add spaces/dashes — function should strip them
        is_valid, error = verify_mfa_token(secret, f"{token[:3]} {token[3:]}")
        assert is_valid is True

    # ── MFAEnrollment ─────────────────────────────────────────────────

    def test_enroll_mfa_returns_enrollment(self):
        """enroll_mfa returns MFAEnrollment with secret, qr, backup codes."""
        enrollment = enroll_mfa("test@example.com")
        assert isinstance(enrollment, MFAEnrollment)
        assert isinstance(enrollment.secret, str)
        assert len(enrollment.secret) > 0
        assert isinstance(enrollment.qr_code, bytes)
        assert len(enrollment.qr_code) > 0
        assert isinstance(enrollment.backup_codes, list)
        assert len(enrollment.backup_codes) == 10

    def test_enroll_mfa_qr_code_png(self):
        """Enrollment QR code is a valid PNG."""
        enrollment = enroll_mfa("test@example.com")
        assert enrollment.qr_code.startswith(b'\x89PNG')

    def test_enroll_mfa_backup_codes_hashed(self):
        """Enrollment backup_code_hashes match the raw codes."""
        enrollment = enroll_mfa("test@example.com")
        assert len(enrollment.backup_codes_hashed) == len(enrollment.backup_codes)
        for raw, hashed in zip(enrollment.backup_codes, enrollment.backup_codes_hashed):
            assert MFAService.hash_backup_code(raw) == hashed

    def test_enroll_mfa_secret_totp_works(self):
        """Enrollment secret is a valid TOTP secret."""
        enrollment = enroll_mfa("test@example.com")
        totp = pyotp.TOTP(enrollment.secret)
        assert totp.now() is not None

    # ── Edge Cases ────────────────────────────────────────────────────

    def test_empty_secret_verify(self):
        """Empty secret for verify_token returns False gracefully."""
        assert MFAService.verify_token("", "123456") is False

    def test_verify_token_none_token(self):
        """None token handled gracefully."""
        secret = MFAService.generate_secret()
        assert MFAService.verify_token(secret, None) is False

    def test_generate_qr_code_empty_uri(self):
        """Empty URI QR generation doesn't crash."""
        qr = MFAService.generate_qr_code("")
        assert isinstance(qr, bytes)