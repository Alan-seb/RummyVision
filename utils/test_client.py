"""
Test client for RummyVision servers

Simple script to test both the CV server and game engine server.
Useful for debugging and verifying the servers are working correctly.

Usage:
    python test_client.py <image_path>  # Test with an image
    python test_client.py               # Test engine with dummy data
"""

import requests
import json
import sys
import os

# Configuration - update these if your servers run on different ports
CV_SERVER_URL = "http://localhost:8000/recognize"
ENGINE_SERVER_URL = "http://localhost:8001/suggest"

def test_cv_server(image_path):
    """
    Tests the card recognition server with an image file.
    
    Uploads the image and prints the detected cards.
    Returns the list of detected cards, or None on error.
    """
    print(f"Testing CV Server with {image_path}...")
    if not os.path.exists(image_path):
        print("Error: Image file not found.")
        return None
        
    with open(image_path, "rb") as f:
        files = {"file": f}
        try:
            response = requests.post(CV_SERVER_URL, files=files)
            if response.status_code == 200:
                print("CV Server Response:")
                print(json.dumps(response.json(), indent=2))
                return response.json().get("cards", [])
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Connection failed: {e}")
            print("Make sure the CV server is running on port 8000")
    return None

def test_engine_server(hand):
    """
    Tests the game engine server with a hand of cards.
    
    Sends a hand and gets discard suggestions back.
    Prints the suggestions with win probabilities.
    """
    print("\nTesting Engine Server...")
    payload = {
        "my_hand": hand,
        "visible": [],  # No visible cards (discard pile, etc.)
        "trials": 500  # More trials = more accurate but slower
    }
    
    try:
        response = requests.post(ENGINE_SERVER_URL, json=payload)
        if response.status_code == 200:
            print("Engine Server Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Make sure the game engine server is running on port 8001")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <image_path>")
        print("Or run without arguments to test engine with dummy data")
        # Default test with dummy data if no image provided
        # Useful for testing the game logic without needing an image
        print("\nRunning default logic test...")
        test_hand = ["A-hearts", "2-hearts", "3-hearts", "K-spades", "5-diamonds"]
        test_engine_server(test_hand)
    else:
        # Test with an actual image file
        image_path = sys.argv[1]
        cards = test_cv_server(image_path)
        if cards:
            # Convert card objects to string format for engine
            # CV server returns {"rank": "A", "suit": "hearts"}
            # Engine expects "A-hearts" format
            hand = [f"{c['rank']}-{c['suit']}" for c in cards]
            test_engine_server(hand)
