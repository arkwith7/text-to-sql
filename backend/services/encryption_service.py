from cryptography.fernet import Fernet
from core.config import get_settings

class EncryptionService:
    def __init__(self):
        settings = get_settings()
        secret_key = settings.secret_key
        if not secret_key:
            raise ValueError("SECRET_KEY is not set in the environment settings.")
        
        # Ensure the key is 32 bytes and URL-safe base64 encoded
        # Fernet keys must be 32 url-safe base64-encoded bytes.
        import base64
        key = base64.urlsafe_b64encode(secret_key.encode('utf-8')[:32].ljust(32, b'\0'))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypts a string."""
        if not data:
            return ""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypts a string."""
        if not encrypted_data:
            return ""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

# Global instance
encryption_service = EncryptionService() 