#!/usr/bin/env python3
"""
Template Checker Script
Verifies that all required template images are present and can be loaded.
"""

import os
import cv2
from pathlib import Path

# Required templates
REQUIRED_RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
REQUIRED_SUITS = ['hearts', 'diamonds', 'clubs', 'spades']

# Get script directory
SCRIPT_DIR = Path(__file__).parent
RANK_DIR = SCRIPT_DIR / "ranks"
SUIT_DIR = SCRIPT_DIR / "suits"

def check_templates():
    """Check if all required templates are present and valid."""
    print("🎴 Template Image Checker")
    print("=" * 50)
    print()
    
    # Check rank templates
    print("Checking RANK templates...")
    print(f"Directory: {RANK_DIR}")
    print()
    
    if not RANK_DIR.exists():
        print(f"❌ ERROR: Directory does not exist: {RANK_DIR}")
        print(f"   Please create the directory first.")
        return False
    
    rank_files = list(RANK_DIR.glob("*"))
    rank_found = {}
    rank_missing = []
    
    for rank in REQUIRED_RANKS:
        # Check for .jpg, .jpeg, or .png
        found = False
        for ext in ['.jpg', '.jpeg', '.png']:
            file_path = RANK_DIR / f"{rank}{ext}"
            if file_path.exists():
                # Try to load it
                img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    rank_found[rank] = str(file_path.name)
                    found = True
                    print(f"  ✅ {rank}: {file_path.name} ({img.shape[1]}x{img.shape[0]} pixels)")
                    break
        
        if not found:
            rank_missing.append(rank)
            print(f"  ❌ {rank}: MISSING")
    
    print()
    print("Checking SUIT templates...")
    print(f"Directory: {SUIT_DIR}")
    print()
    
    if not SUIT_DIR.exists():
        print(f"❌ ERROR: Directory does not exist: {SUIT_DIR}")
        print(f"   Please create the directory first.")
        return False
    
    suit_found = {}
    suit_missing = []
    
    for suit in REQUIRED_SUITS:
        found = False
        for ext in ['.jpg', '.jpeg', '.png']:
            file_path = SUIT_DIR / f"{suit}{ext}"
            if file_path.exists():
                img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    suit_found[suit] = str(file_path.name)
                    found = True
                    print(f"  ✅ {suit}: {file_path.name} ({img.shape[1]}x{img.shape[0]} pixels)")
                    break
        
        if not found:
            suit_missing.append(suit)
            print(f"  ❌ {suit}: MISSING")
    
    # Summary
    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Rank templates: {len(rank_found)}/{len(REQUIRED_RANKS)} found")
    print(f"Suit templates: {len(suit_found)}/{len(REQUIRED_SUITS)} found")
    print()
    
    if rank_missing or suit_missing:
        print("❌ INCOMPLETE - Missing templates:")
        if rank_missing:
            print(f"   Ranks: {', '.join(rank_missing)}")
        if suit_missing:
            print(f"   Suits: {', '.join(suit_missing)}")
        print()
        print("📖 See TEMPLATE_GUIDE.md for instructions on creating templates.")
        return False
    else:
        print("✅ ALL TEMPLATES PRESENT AND VALID!")
        print()
        print("You're ready to use the card recognition system!")
        return True

if __name__ == "__main__":
    try:
        success = check_templates()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

