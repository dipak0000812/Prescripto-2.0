"""
Generates RS256 RSA keypair for JWT authentication and outputs PEM strings for .env.
"""
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    
    return private_pem, public_pem

if __name__ == "__main__":
    priv, pub = generate_keypair()
    print("=== PRIVATE KEY (JWT_PRIVATE_KEY) ===")
    print(repr(priv))
    print("\n=== PUBLIC KEY (JWT_PUBLIC_KEY) ===")
    print(repr(pub))
