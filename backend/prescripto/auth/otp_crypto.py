"""
Cryptographic Utilities: OTP generation and verification.
"""
import secrets
import string
import hashlib
from datetime import datetime, timedelta, timezone

def generate_secure_otp(length: int = 6) -> str:
    """Generates a secure numeric OTP."""
    alphabet = string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_otp(otp: str, salt: str) -> str:
    """Hashes an OTP with a salt for secure storage."""
    # Using SHA-256 for integrity. OTPs are short-lived.
    return hashlib.sha256((otp + salt).encode('utf-8')).hexdigest()

def verify_otp_secure(input_otp: str, hashed_otp: str, salt: str) -> bool:
    """Verifies an OTP against a hash in constant time."""
    import hmac
    computed_hash = hash_otp(input_otp, salt)
    return hmac.compare_digest(computed_hash, hashed_otp)
