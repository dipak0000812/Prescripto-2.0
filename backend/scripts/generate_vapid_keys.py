"""
Generate VAPID Keys for Web Push Notifications in Prescripto 2.0.
"""
import base64
from py_vapid import Vapid
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def generate_vapid_keypair():
    vapid = Vapid()
    vapid.generate_keys()
    raw_pub = vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    public_key_b64 = base64.urlsafe_b64encode(raw_pub).rstrip(b"=").decode("utf-8")
    private_pem = vapid.private_pem().decode("utf-8").strip()

    print("=" * 60)
    print("PRESCRIPTO 2.0 — VAPID KEYS GENERATED")
    print("=" * 60)
    print("\nVAPID_PUBLIC_KEY:")
    print(public_key_b64)
    print("\nVAPID_PRIVATE_KEY:")
    print(private_pem.replace("\n", "\\n"))
    print("\nVAPID_CLAIMS_SUB:")
    print("mailto:support@prescripto.local")
    print("=" * 60)
    return public_key_b64, private_pem


if __name__ == "__main__":
    generate_vapid_keypair()

