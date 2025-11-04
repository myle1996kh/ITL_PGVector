"""
Database Rebuild Script

This script will:
1. Drop all existing tables
2. Run all Alembic migrations from scratch
3. Display summary of created data

Usage:
    python rebuild_database.py
"""

import subprocess
import sys
from pathlib import Path

def print_banner(text):
    """Print a formatted banner."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"➤ {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main rebuild process."""

    print_banner("AgentHub Database Rebuild Script")

    print("⚠️  WARNING: This will DROP ALL TABLES and rebuild from scratch!")
    print("⚠️  All existing data will be LOST!")
    print()

    # Confirm with user
    response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n✗ Rebuild cancelled.")
        sys.exit(0)

    print()
    print_banner("Step 1: Downgrade Database (Drop All Tables)")

    # Downgrade to base (drops all tables)
    if not run_command(
        "alembic downgrade base",
        "Dropping all existing tables"
    ):
        print("\n✗ Failed to drop tables. Aborting.")
        sys.exit(1)

    print_banner("Step 2: Run Migrations")

    # Run all migrations
    if not run_command(
        "alembic upgrade head",
        "Running all migrations (001, 002, 003)"
    ):
        print("\n✗ Migration failed. Aborting.")
        sys.exit(1)

    print_banner("Step 3: Verify Database State")

    # Show current migration version
    if not run_command(
        "alembic current",
        "Checking current migration version"
    ):
        print("\n⚠️  Could not verify migration version")

    print_banner("Database Rebuild Complete!")

    print("✓ All tables created successfully")
    print("✓ Seed data inserted:")
    print("  - 5 Base Tools (HTTP_GET, HTTP_POST, RAG, DB_QUERY, OCR)")
    print("  - 4 Output Formats (structured_json, markdown_table, chart_data, summary_text)")
    print("  - 4 LLM Models (GPT-4o-mini, GPT-4o, Gemini 1.5 Pro, Claude 3.5 Sonnet)")
    print("  - 4 Tool Configs (get_customer_debt, track_shipment, search_knowledge_base, get_sales_analytics)")
    print("  - 4 Agents (SupervisorAgent, AgentDebt, AgentShipment, AgentAnalysis)")
    print("  - 1 Demo Tenant (Demo Company)")
    print("  - Widget Configuration for Demo Tenant")
    print()
    print("⚠️  IMPORTANT NEXT STEPS:")
    print("  1. Update the encrypted_api_key in tenant_llm_configs table")
    print("  2. Configure your .env file with:")
    print("     - DATABASE_URL")
    print("     - FERNET_KEY (for encryption)")
    print("     - JWT_PUBLIC_KEY (for authentication)")
    print()
    print("  3. Test the setup:")
    print("     python -m pytest tests/")
    print()
    print("="*70)

if __name__ == "__main__":
    # Change to backend directory
    backend_dir = Path(__file__).parent
    import os
    os.chdir(backend_dir)

    main()
