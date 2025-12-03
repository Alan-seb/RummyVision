# Quick Start Guide

## 🚀 Fastest Way to Get Started

### Backend (5 minutes)

1. **Navigate to server directory:**
   ```bash
   cd server
   ```

2. **Run setup script:**
   ```bash
   ./setup.sh
   ```
   Or manually:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Add template images** (REQUIRED):
   - Put rank images (A.jpg, K.jpg, etc.) in `templates/ranks/`
   - Put suit images (hearts.jpg, etc.) in `templates/suits/`

4. **Start servers** (in two separate terminals):
   
   Terminal 1:
   ```bash
   cd server
   source venv/bin/activate
   python3 card_cv_server.py
   ```
   
   Terminal 2:
   ```bash
   cd server
   source venv/bin/activate
   python3 rummy_engine.py
   ```

### iOS App (5 minutes)

1. **Find your Mac's IP:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
   (Look for something like `192.168.1.5`)

2. **Open in Xcode:**
   - Open `iphone-app/` folder in Xcode

3. **Set server IP:**
   - Open `NetworkManager.swift`
   - Replace the default IP with your Mac's IP:
     ```swift
     return ProcessInfo.processInfo.environment["RUMMY_SERVER_URL"] ?? "http://YOUR_IP_HERE"
     ```

4. **Build and run:**
   - Connect iPhone via USB
   - Select iPhone as target device
   - Press ▶️ (Play button) or `Cmd + R`
   - Grant camera permissions when prompted

### Test It!

1. Point iPhone camera at playing cards
2. Tap capture button
3. See detected cards
4. Tap "Get Suggestion" for discard recommendations

## ⚠️ Common Issues

**Servers won't start?**
- Make sure virtual environment is activated: `source venv/bin/activate`
- Check if ports 8000/8001 are in use: `lsof -i :8000`

**iOS app can't connect?**
- Verify both servers are running
- Check iPhone and Mac are on same Wi-Fi
- Verify IP address in NetworkManager.swift
- Try accessing `http://YOUR_IP:8000` from iPhone Safari

**No cards detected?**
- Check templates are loaded: `http://localhost:8000/`
- Verify template images are in correct directories
- Improve lighting and card positioning

## 📚 Full Documentation

See `BUILD.md` for detailed instructions and troubleshooting.

