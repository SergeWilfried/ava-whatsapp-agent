#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to clear short-term memory (conversation history) based on environment variable.

This script deletes the SQLite database file used by LangGraph's checkpointer
to store conversation history. It only runs if CLEAR_SHORT_TERM_MEMORY=true.

Usage:
    # Set environment variable and run
    export CLEAR_SHORT_TERM_MEMORY=true
    python scripts/clear_short_term_memory.py

    # Or run directly with the variable
    CLEAR_SHORT_TERM_MEMORY=true python scripts/clear_short_term_memory.py

Environment Variables:
    CLEAR_SHORT_TERM_MEMORY: Set to 'true', '1', 'yes' to enable clearing
    SHORT_TERM_MEMORY_DB_PATH: Path to the SQLite database (default: /app/data/memory.db)
"""

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_companion.settings import settings


def should_clear_memory() -> bool:
    """Check if the environment variable is set to clear memory."""
    clear_flag = os.getenv("CLEAR_SHORT_TERM_MEMORY", "").lower()
    return clear_flag in ("true", "1", "yes", "on")


def clear_short_term_memory() -> bool:
    """Clear the short-term memory database.

    Returns:
        bool: True if cleared successfully, False otherwise
    """
    db_path = Path(settings.SHORT_TERM_MEMORY_DB_PATH)

    if not db_path.exists():
        safe_print(f"INFO: Database file not found: {db_path}")
        safe_print("   No memory to clear.")
        return True

    try:
        # Get file size before deletion
        size_mb = db_path.stat().st_size / (1024 * 1024)

        # Delete the database file
        db_path.unlink()

        safe_print(f"SUCCESS: Short-term memory cleared!")
        safe_print(f"   Deleted: {db_path}")
        safe_print(f"   Size: {size_mb:.2f} MB")
        safe_print(f"   All conversation histories have been removed.")

        return True

    except PermissionError:
        safe_print(f"ERROR: Permission denied: Cannot delete {db_path}")
        safe_print(f"   The database may be in use. Stop the application and try again.")
        return False

    except Exception as e:
        safe_print(f"ERROR: Error clearing memory: {e}")
        return False


def safe_print(text: str):
    """Print text with fallback for systems with encoding issues."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: Remove emojis and special characters
        import re
        ascii_text = re.sub(r'[^\x00-\x7F]+', '', text)
        print(ascii_text)


def main():
    """Main entry point for the script."""
    safe_print("=" * 60)
    safe_print("Short-Term Memory Cleaner")
    safe_print("=" * 60)
    safe_print("")

    # Check if clearing is enabled
    if not should_clear_memory():
        safe_print("WARNING: Memory clearing is DISABLED")
        print()
        print("To enable, set the environment variable:")
        print("  export CLEAR_SHORT_TERM_MEMORY=true")
        print()
        print("Or run with:")
        print("  CLEAR_SHORT_TERM_MEMORY=true python scripts/clear_short_term_memory.py")
        print()
        sys.exit(0)

    safe_print(f"Database path: {settings.SHORT_TERM_MEMORY_DB_PATH}")
    safe_print("")

    # Confirm action
    safe_print("WARNING: This will delete ALL conversation histories!")
    safe_print("   This action cannot be undone.")
    safe_print("")

    # In non-interactive environments, proceed automatically
    if not sys.stdin.isatty():
        safe_print("Running in non-interactive mode. Proceeding automatically...")
        success = clear_short_term_memory()
    else:
        # Interactive confirmation
        response = input("Do you want to proceed? (yes/no): ").lower().strip()

        if response not in ("yes", "y"):
            safe_print("")
            safe_print("Operation cancelled.")
            sys.exit(0)

        safe_print("")
        success = clear_short_term_memory()

    safe_print("")
    safe_print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
