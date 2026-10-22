"""Multi-Factor Authentication service using TOTP."""

import hashlib
import hmac
import secrets
from typing import Tuple

import pyotp
import qrcode
from io import BytesIO

from app.config import get_settings

settings = get_settings()


class MFAService:
    """Multi-Factor Authentication service."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new MFA secret key."""
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, email: str, issuer: str = None) -> str:
        """Generate TOTP URI for QR code."""
        issuer = issuer or getattr(settings, 'mfa_issuer', settings.jwt_issuer)
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )

    @staticmethod
    def generate_qr_code(uri: str) -> bytes:
        """Generate QR code image bytes."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def verify_token(secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token."""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)

    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """Generate backup recovery codes."""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()
            # Format as XXXX-XXXX for readability
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes

    @staticmethod
    def hash_backup_code(code: str) -> str:
        """Hash backup code for storage."""
        # Remove dashes and normalize
        code = code.replace("-", "").upper()
        return hashlib.sha256(code.encode()).hexdigest()

    @staticmethod
    def verify_backup_code(provided_code: str, stored_hash: str) -> bool:
        """Verify backup code against stored hash."""
        provided_hash = MFAService.hash_backup_code(provided_code)
        return hmac.compare_digest(provided_hash, stored_hash)


class MFAEnrollment:
    """MFA enrollment data."""
    
    def __init__(self, secret: str, qr_code: bytes, backup_codes: list[str]):
        self.secret = secret
        self.qr_code = qr_code
        self.backup_codes = backup_codes
        self.backup_codes_hashed = [MFAService.hash_backup_code(code) for code in backup_codes]


def enroll_mfa(email: str) -> MFAEnrollment:
    """Enroll a user in MFA."""
    secret = MFAService.generate_secret()
    uri = MFAService.get_totp_uri(secret, email)
    qr_code = MFAService.generate_qr_code(uri)
    backup_codes = MFAService.generate_backup_codes()
    
    return MFAEnrollment(secret, qr_code, backup_codes)


def verify_mfa_token(secret: str, token: str) -> Tuple[bool, str]:
    """
    Verify MFA token.
    Returns (is_valid, error_message).
    """
    # Remove spaces and dashes
    token = token.replace(" ", "").replace("-", "")
    
    # Check if it's a backup code (8 characters)
    if len(token) == 8:
        return False, "Use backup codes through the backup code endpoint"
    
    # Verify TOTP token (6 digits)
    if len(token) != 6 or not token.isdigit():
        return False, "Invalid token format"
    
    if MFAService.verify_token(secret, token):
        return True, ""
    
    return False, "Invalid verification code"