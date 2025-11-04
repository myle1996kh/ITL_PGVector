"""
Update OpenRouter API Key for Tenant

After you get a new API key from https://openrouter.ai/keys:
1. Update backend/.env with: OPENROUTER_API_KEY=sk-or-v1-YOUR_NEW_KEY
2. Run this script: python update_api_key.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import get_db, settings
from sqlalchemy import text
from cryptography.fernet import Fernet

TENANT_ID = "128e9b53-7610-453f-a2d4-a5d2537a36c4"

def main():
    print("="*70)
    print("Update OpenRouter API Key for Demo Company Tenant")
    print("="*70)

    # Check if API key is set
    if not settings.OPENROUTER_API_KEY:
        print("\n❌ ERROR: OPENROUTER_API_KEY not found in .env")
        print("\nSteps:")
        print("1. Get API key from: https://openrouter.ai/keys")
        print("2. Add to backend/.env: OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY")
        print("3. Run this script again")
        return False

    print(f"\nAPI Key from .env: {settings.OPENROUTER_API_KEY[:30]}...")

    # Encrypt the new key
    fernet = Fernet(settings.FERNET_KEY.encode())
    encrypted_key = fernet.encrypt(settings.OPENROUTER_API_KEY.encode()).decode()

    # Update database
    db = next(get_db())

    try:
        db.execute(text("""
            UPDATE tenant_llm_configs
            SET encrypted_api_key = :key
            WHERE tenant_id = :tenant_id
        """), {
            "key": encrypted_key,
            "tenant_id": TENANT_ID
        })
        db.commit()

        print(f"\n✓ API key updated for tenant {TENANT_ID}")
        print("\nYou can now test AgentGuidance:")
        print('  curl -X POST "http://localhost:8000/api/128e9b53-7610-453f-a2d4-a5d2537a36c4/chat" \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"message": "Hướng dẫn QUY TRÌNH VẬN HÀNH ĐƠN HÀNG", "user_id": "demo"}\'')

        return True

    except Exception as e:
        print(f"\n❌ Failed to update: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
