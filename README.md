# RummyVision

**RummyVision** is an intelligent card game assistant that combines computer vision with Monte Carlo simulation to help you make better decisions in Rummy. Point your iPhone camera at your hand, and get real-time card recognition and strategic discard suggestions powered by AI.

The system consists of an iOS app for card capture and Python FastAPI servers for card recognition and game strategy. Built as a weekend project to explore computer vision and game theory, it's now ready for others to use and improve.

## What is RummyVision?

RummyVision is a practical tool for Rummy players who want to improve their game. Instead of manually tracking cards and calculating probabilities, you can simply point your phone's camera at your hand and get instant strategic advice. The app uses OpenCV for card detection and Monte Carlo simulation to evaluate different discard strategies, giving you ranked suggestions with win probability estimates.

This project demonstrates how modern computer vision and game theory algorithms can be combined to create useful real-world applications. It's built with Python FastAPI on the backend and SwiftUI on iOS, making it easy to extend and customize.

### Why I Built This

I've always been interested in both computer vision and game theory, and Rummy seemed like the perfect project to combine them. The card recognition part was a fun challenge - getting OpenCV to reliably detect cards in various lighting conditions took some tweaking. The Monte Carlo simulation for strategy suggestions was equally interesting - it's fascinating how well random sampling works for evaluating game states.

The result is a working system that can actually help improve your Rummy game, and the codebase is structured so others can learn from it or build upon it.

## Project Structure
- `iphone-app/`: SwiftUI iOS application for card capture.
- `server/`: Python FastAPI servers for CV and Game Logic.
- `utils/`: Testing utilities.

## Features

- **Card Recognition**: Computer vision-based card detection and identification
- **Strategy Engine**: Monte Carlo simulation for optimal discard suggestions
- **Production-Ready**: Comprehensive error handling, logging, and validation
- **Configurable**: Environment variables and runtime configuration
- **Cross-Platform**: iOS app with Python backend

## Setup Instructions

### 1. Python Backend

#### Prerequisites
- Python 3.8 or higher
- pip package manager

#### Installation

1. Navigate to the server directory:
   ```bash
   cd server
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Important**: You must add template images for card recognition.
   - Place rank images (A.jpg, K.jpg, etc.) in `server/templates/ranks/`
   - Place suit images (hearts.jpg, etc.) in `server/templates/suits/`
   - See `server/templates/README.txt` for details.
   - Supported formats: JPG, JPEG, PNG

#### Configuration (Optional)

You can configure the servers using environment variables:

**CV Server** (port 8000):
```bash
export HOST=0.0.0.0
export PORT=8000
export TEMPLATE_DIR=templates
export MIN_RANK_SCORE=0.3
export MIN_SUIT_SCORE=0.3
```

**Game Engine** (port 8001):
```bash
export HOST=0.0.0.0
export PORT=8001
```

### 2. Running the Servers

You need to run two separate server processes.

**Terminal 1 (CV Server):**
```bash
cd server
python card_cv_server.py
```
Runs on port 8000 by default. Check the logs for template loading status.

**Terminal 2 (Game Engine):**
```bash
cd server
python rummy_engine.py
```
Runs on port 8001 by default.

**Health Checks:**
- CV Server: `http://localhost:8000/`
- Game Engine: `http://localhost:8001/`
- Reload templates: `http://localhost:8000/templates/reload`

### 3. iOS App Setup

1. Open `iphone-app/` in Xcode (requires Xcode 14+ and iOS 16+).

2. **Configure Server URL**:
   - Option 1: Set environment variable `RUMMY_SERVER_URL` in Xcode scheme
   - Option 2: Use UserDefaults (the app will prompt or you can set it programmatically)
   - Option 3: Modify `NetworkManager.swift` to set a default IP address
   
   The server URL should be your laptop's local IP address (e.g., `http://192.168.1.5`).
   Find your IP:
   - macOS/Linux: `ifconfig | grep "inet "`
   - Windows: `ipconfig`

3. Build and run on a physical iPhone (camera required - simulator won't work).

4. Ensure iPhone and Laptop are on the same Wi-Fi network.

5. Grant camera permissions when prompted.

## Usage

1. Start both Python servers (CV Server and Game Engine).
2. Open the iOS app on your iPhone.
3. Point camera at your hand of cards.
4. Tap the capture button.
5. View detected cards (filtered by confidence scores).
6. Tap "Get Suggestion" to see recommended discards with win probabilities.

## API Endpoints

### CV Server (Port 8000)

- `POST /recognize` - Upload image for card recognition
  - Accepts: multipart/form-data with image file
  - Returns: List of detected cards with confidence scores

- `GET /` - Health check and template status
- `GET /templates/reload` - Reload templates from disk

### Game Engine (Port 8001)

- `POST /suggest` - Get discard suggestions
  - Body: `{"my_hand": ["A-hearts", "K-spades", ...], "visible": [], "trials": 200, "max_draws": 5}`
  - Returns: Ranked list of discard suggestions with win probabilities

- `GET /` - Health check
- `GET /deck/validate?card=A-hearts` - Validate card format

## Accuracy Tips

- **Lighting**: Ensure good, even lighting. Shadows can interfere with contour detection.
- **Background**: Use a plain, dark background for best contrast with white cards.
- **Templates**: The quality of your template images directly impacts recognition accuracy.
- **Stability**: Hold the camera steady during capture.
- **Card Spacing**: Ensure cards are well-separated and not overlapping.
- **Angle**: Cards should be relatively flat, not at extreme angles.

## Production Considerations

### Security
- In production, configure CORS to allow only specific origins
- Add authentication/authorization if exposing to the internet
- Use HTTPS in production
- Validate and sanitize all inputs

### Performance
- Consider using a production ASGI server like Gunicorn with Uvicorn workers
- Implement rate limiting
- Add caching for template matching results
- Consider using Redis for session management

### Monitoring
- Logs are configured with timestamps and log levels
- Monitor template loading status
- Track API response times
- Set up health check monitoring

### Scaling
- Consider containerizing with Docker
- Use a reverse proxy (nginx) for load balancing
- Implement horizontal scaling for the game engine
- Use a message queue for async processing if needed

## Troubleshooting

### Cards Not Detected
- Check template loading: `GET http://localhost:8000/`
- Verify templates are in correct directories
- Check image quality and lighting
- Review confidence scores in response

### Server Connection Errors
- Verify both servers are running
- Check firewall settings
- Ensure iPhone and laptop are on same network
- Verify IP address in NetworkManager

### Low Recognition Accuracy
- Improve template image quality
- Adjust MIN_RANK_SCORE and MIN_SUIT_SCORE thresholds
- Ensure templates match your card design
- Try reloading templates: `GET http://localhost:8000/templates/reload`

## Future Improvements

- Train a YOLO model for more robust detection in varied lighting
- Use CoreML on-device to remove the need for image upload, speeding up the process
- Add support for multiple card designs
- Implement real-time video processing
- Add game state tracking and history
- Support for multiple players

## How It Works

1. **Card Recognition**: Uses OpenCV template matching to detect and identify playing cards from camera images
2. **Game Analysis**: Implements Monte Carlo simulation to evaluate different discard strategies
3. **Strategy Suggestions**: Provides ranked discard recommendations with win probability estimates

The system uses a two-server architecture for separation of concerns - one handles computer vision, the other handles game logic. This makes it easier to scale and maintain.

## Technical Details

- **Backend**: Python 3.8+, FastAPI, OpenCV, NumPy
- **Frontend**: SwiftUI, iOS 16+
- **Architecture**: RESTful API with CORS support for cross-platform access
- **Algorithm**: Monte Carlo simulation with configurable trial counts

## Known Limitations

- Card recognition accuracy depends heavily on lighting and template image quality
- Currently optimized for standard playing card designs
- Requires manual template image setup
- Best results with plain backgrounds and good lighting

## Future Improvements

- Train a YOLO model for more robust detection in varied lighting
- Use CoreML on-device to remove the need for image upload, speeding up the process
- Add support for multiple card designs
- Implement real-time video processing
- Add game state tracking and history
- Support for multiple players

## License

MIT License - feel free to use this project for learning or building your own card game assistant.

## Contributing

Contributions welcome! Some areas that could use help:
- Better template matching algorithms
- Support for different card designs
- Performance optimizations
- UI/UX improvements
- Documentation improvements
