"""
Update Tenant API Key Script

This script helps you encrypt and update the LLM API key for a tenant.

Usage:
    python update_tenant_api_key.py <tenant_id> <api_key>

Example:
    python update_tenant_api_key.py 550e8400-e29b-41d4-a716-446655440000 sk-proj-...
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.tenant_llm_config import TenantLLMConfig
from src.utils.encryption import encrypt_fernet
from src.config import settings


def update_api_key(tenant_id: str, api_key: str):
    """Update the API key for a tenant."""

    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Find tenant LLM config
        config = session.query(TenantLLMConfig).filter_by(
            tenant_id=tenant_id
        ).first()

        if not config:
            print(f"✗ No LLM config found for tenant {tenant_id}")
            print(f"  Available tenants:")

            # Show available tenants
            from src.models.tenant import Tenant
            tenants = session.query(Tenant).all()
            for tenant in tenants:
                print(f"    - {tenant.name}: {tenant.tenant_id}")

            return False

        # Encrypt the API key
        print(f"➤ Encrypting API key...")
        encrypted_key = encrypt_fernet(api_key)

        # Update the config
        config.encrypted_api_key = encrypted_key

        session.commit()

        print(f"✓ API key updated successfully for tenant {tenant_id}")
        print(f"  Tenant: {config.tenant.name}")
        print(f"  LLM Model: {config.llm_model.model_name}")
        print(f"  Encrypted Key (first 30 chars): {encrypted_key[:30]}...")

        return True

    except Exception as e:
        session.rollback()
        print(f"✗ Error updating API key: {e}")
        return False

    finally:
        session.close()


def main():
    """Main function."""

    if len(sys.argv) < 3:
        print("Usage: python update_tenant_api_key.py <tenant_id> <api_key>")
        print()
        print("Example:")
        print("  python update_tenant_api_key.py 550e8400-e29b-41d4-a716-446655440000 sk-proj-...")
        print()

        # Try to show available tenants
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from src.models.tenant import Tenant
            from src.config import settings

            engine = create_engine(settings.DATABASE_URL)
            Session = sessionmaker(bind=engine)
            session = Session()

            tenants = session.query(Tenant).all()
            if tenants:
                print("Available tenants:")
                for tenant in tenants:
                    print(f"  - {tenant.name}: {tenant.tenant_id}")

            session.close()

        except Exception as e:
            print(f"(Could not load tenants: {e})")

        sys.exit(1)

    tenant_id = sys.argv[1]
    api_key = sys.argv[2]

    # Validate API key format (basic check)
    if len(api_key) < 20:
        print("✗ API key seems too short. Please provide a valid API key.")
        sys.exit(1)

    # Update the key
    success = update_api_key(tenant_id, api_key)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
