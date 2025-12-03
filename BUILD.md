# Build Guide - Rummy Assistant

This guide will walk you through building and running the Rummy Assistant system from scratch.

## Prerequisites

### For Backend (Python Servers)
- Python 3.8 or higher
- pip (Python package manager)
- Terminal/Command Prompt access

### For iOS App
- macOS with Xcode 14+ installed
- Physical iPhone (camera required - simulator won't work)
- Apple Developer account (for device deployment)
- iPhone and Mac on the same Wi-Fi network

## Step-by-Step Build Instructions

### Part 1: Backend Setup

#### Step 1.1: Navigate to Server Directory
```bash
cd /Users/alox/Developer/AI_RUMMY/rummy-assistant/server
```

#### Step 1.2: Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### Step 1.3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI
- Uvicorn
- OpenCV
- NumPy
- Pydantic
- And other dependencies

#### Step 1.4: Prepare Template Images

**CRITICAL**: The card recognition won't work without template images!

1. Create template images for each rank and suit:
   - **Ranks**: A, 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K
   - **Suits**: hearts, diamonds, clubs, spades

2. Place rank images in: `server/templates/ranks/`
   - Example: `A.jpg`, `K.jpg`, `10.jpg`, etc.

3. Place suit images in: `server/templates/suits/`
   - Example: `hearts.jpg`, `diamonds.jpg`, etc.

**Tip**: Take photos of your actual playing cards against a plain background, crop to just the rank/suit area.

#### Step 1.5: Test Backend Installation

Verify Python can import the required packages:
```bash
python3 -c "import cv2, numpy, fastapi; print('All packages installed successfully!')"
```

### Part 2: Running the Servers

You need **TWO terminal windows** - one for each server.

#### Terminal 1: Start CV Server

```bash
cd /Users/alox/Developer/AI_RUMMY/rummy-assistant/server
source venv/bin/activate  # If using venv
python3 card_cv_server.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Check if templates loaded:**
- Open browser: `http://localhost:8000/`
- Should show template count (e.g., "rank_templates": 13, "suit_templates": 4)

#### Terminal 2: Start Game Engine

```bash
cd /Users/alox/Developer/AI_RUMMY/rummy-assistant/server
source venv/bin/activate  # If using venv
python3 rummy_engine.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Test the engine:**
- Open browser: `http://localhost:8001/`
- Should show: `{"status": "ok", "service": "rummy_engine"}`

### Part 3: iOS App Setup

#### Step 3.1: Find Your Mac's IP Address

**On macOS:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Look for something like: `inet 192.168.1.5` (this is your local IP)

**Alternative method:**
```bash
ipconfig getifaddr en0
```

#### Step 3.2: Open Project in Xcode

1. Open Xcode
2. File → Open → Navigate to `/Users/alox/Developer/AI_RUMMY/rummy-assistant/iphone-app/`
3. Select the project folder

#### Step 3.3: Configure Server URL

**Option A: Set Default IP in Code (Easiest)**

1. Open `NetworkManager.swift`
2. Find the line with the default IP
3. Replace with your Mac's IP address:
   ```swift
   return ProcessInfo.processInfo.environment["RUMMY_SERVER_URL"] ?? "http://192.168.1.5"
   ```
   (Replace `192.168.1.5` with your actual IP)

**Option B: Set Environment Variable in Xcode**

1. In Xcode: Product → Scheme → Edit Scheme
2. Run → Arguments → Environment Variables
3. Add: `RUMMY_SERVER_URL` = `http://YOUR_IP_ADDRESS`

**Option C: Set at Runtime (Advanced)**

The app supports UserDefaults - you can add a settings screen later.

#### Step 3.4: Configure Signing

1. Select the project in Xcode navigator
2. Select your target
3. Go to "Signing & Capabilities"
4. Select your Team (Apple Developer account)
5. Xcode will automatically create a provisioning profile

#### Step 3.5: Connect Your iPhone

1. Connect iPhone to Mac via USB
2. Unlock iPhone and trust the computer if prompted
3. In Xcode, select your iPhone from the device dropdown (top toolbar)

#### Step 3.6: Build and Run

1. Click the Play button (▶️) or press `Cmd + R`
2. Wait for build to complete
3. App will install and launch on your iPhone
4. Grant camera permissions when prompted

### Part 4: Testing the System

#### Test 1: Verify Servers are Running

**CV Server:**
```bash
curl http://localhost:8000/
```

**Game Engine:**
```bash
curl http://localhost:8001/
```

#### Test 2: Test Card Recognition (Optional)

If you have the test client:
```bash
cd utils
python3 test_client.py path/to/test_image.jpg
```

#### Test 3: Test from iOS App

1. Open the app on your iPhone
2. Point camera at playing cards
3. Tap the capture button
4. Check if cards are detected
5. Tap "Get Suggestion" to test the game engine

### Part 5: Troubleshooting

#### Backend Issues

**"Module not found" errors:**
```bash
# Make sure venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

**"Templates not found" warning:**
- Check that `server/templates/ranks/` and `server/templates/suits/` exist
- Verify template images are in correct format (JPG/PNG)
- Check file names match expected format

**Port already in use:**
```bash
# Find what's using the port
lsof -i :8000
lsof -i :8001

# Kill the process or change PORT environment variable
```

#### iOS App Issues

**"Cannot connect to server":**
- Verify both servers are running
- Check iPhone and Mac are on same Wi-Fi network
- Verify IP address in NetworkManager.swift
- Check Mac firewall isn't blocking connections
- Try accessing `http://YOUR_IP:8000` from iPhone's Safari

**"Camera not working":**
- Ensure you're using a physical device (not simulator)
- Check camera permissions in iPhone Settings
- Restart the app

**Build errors:**
- Clean build folder: Product → Clean Build Folder (Shift + Cmd + K)
- Delete DerivedData: Xcode → Preferences → Locations → DerivedData → Delete
- Restart Xcode

### Part 6: Production Deployment (Optional)

For production use, consider:

1. **Use a production ASGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker card_cv_server:app
   ```

2. **Add reverse proxy (nginx):**
   - Configure nginx to proxy requests
   - Add SSL/TLS certificates
   - Configure CORS properly

3. **Set up monitoring:**
   - Add logging to file
   - Set up health check monitoring
   - Monitor server resources

## Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Template images added to `server/templates/`
- [ ] CV Server running on port 8000
- [ ] Game Engine running on port 8001
- [ ] Mac IP address found
- [ ] Server URL configured in iOS app
- [ ] iPhone connected and selected in Xcode
- [ ] App built and installed on iPhone
- [ ] Camera permissions granted
- [ ] Tested card capture
- [ ] Tested suggestion engine

## Next Steps

Once everything is working:
1. Test with different lighting conditions
2. Fine-tune template images for better accuracy
3. Adjust confidence thresholds if needed
4. Add more features (settings screen, history, etc.)

## Getting Help

If you encounter issues:
1. Check server logs in terminal windows
2. Check Xcode console for iOS app errors
3. Verify all prerequisites are met
4. Review the troubleshooting section above

Good luck! 🎴

