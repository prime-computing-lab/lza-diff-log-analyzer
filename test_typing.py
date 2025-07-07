#!/usr/bin/env python3
"""
Test script to verify interactive session typing works correctly
"""

import asyncio
import sys
from rich.console import Console
from src.interactive.simple_session import SimpleInteractiveSession


async def main():
    """Test the simple interactive session"""
    console = Console()
    
    print("=" * 60)
    print("TESTING SIMPLIFIED INTERACTIVE SESSION")
    print("=" * 60)
    print()
    print("This test will start the interactive session.")
    print("Try typing some text to verify it's visible as you type.")
    print("Test commands: 'help', 'summary', 'exit'")
    print()
    print("Starting session in 3 seconds...")
    
    await asyncio.sleep(3)
    
    # Create session with no analysis data (will use rule-based responses)
    session = SimpleInteractiveSession(console)
    
    try:
        await session.start(input_dir=".", analysis_results=None)
    except KeyboardInterrupt:
        print("\nTest completed - session ended by user")
    except Exception as e:
        print(f"Error during test: {e}")


if __name__ == "__main__":
    asyncio.run(main())