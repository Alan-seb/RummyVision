"""
Card Recognition Server for RummyVision

This server handles the computer vision side of things - detecting cards in images
and identifying their rank and suit using template matching.

I went with template matching over a full ML model because:
1. Faster to implement and iterate on
2. Works well enough for controlled environments
3. No training data needed (just template images)

TODO: Consider switching to YOLO or similar for better robustness in varied lighting
TODO: Maybe add support for multiple card designs/styles
"""

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging
from pathlib import Path

# Configure logging - keeping it simple for now
# Could add file logging later if needed, but console is fine for development
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Card Recognition Server",
    description="Computer vision server for recognizing playing cards",
    version="1.0.0"
)

# Add CORS middleware for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
# These can be overridden via environment variables for different card sizes
# I found these values work well for standard playing cards, but YMMV
# If you're using non-standard cards, you'll probably need to adjust these
TEMPLATE_DIR = os.getenv("TEMPLATE_DIR", "templates")
RANK_DIR = os.path.join(TEMPLATE_DIR, "ranks")
SUIT_DIR = os.path.join(TEMPLATE_DIR, "suits")

# Standard card dimensions after warping - adjust if your cards are different
# These are the dimensions we normalize cards to before template matching
# Makes matching more reliable since all cards are the same size
CARD_WIDTH = int(os.getenv("CARD_WIDTH", "200"))
CARD_HEIGHT = int(os.getenv("CARD_HEIGHT", "300"))

# Region of interest for rank/suit detection (top-left corner of card)
# This assumes rank is at the top and suit is below it (standard card layout)
# Had to tweak these values quite a bit to get good results - took some trial and error
CORNER_X = int(os.getenv("CORNER_X", "0"))
CORNER_Y = int(os.getenv("CORNER_Y", "0"))
CORNER_W = int(os.getenv("CORNER_W", "35"))
CORNER_H = int(os.getenv("CORNER_H", "85"))

# Minimum confidence thresholds - lower = more permissive, higher = stricter
# Found 0.3 to be a good balance between false positives and false negatives
# If you're getting too many wrong cards, bump these up. Too few cards detected? Lower them.
MIN_RANK_SCORE = float(os.getenv("MIN_RANK_SCORE", "0.3"))
MIN_SUIT_SCORE = float(os.getenv("MIN_SUIT_SCORE", "0.3"))
MIN_CARD_AREA = int(os.getenv("MIN_CARD_AREA", "1000"))  # Filter out noise/small artifacts

# Global template storage - loaded once at startup for performance
# Could cache these in memory or use a more sophisticated approach, but this works fine
# Templates are loaded at startup and reused for all requests
rank_templates = {}
suit_templates = {}

def load_templates():
    """
    Loads rank and suit templates from disk.
    
    Templates should be grayscale images of just the rank/suit area.
    The filename (without extension) is used as the identifier.
    E.g., "A.jpg" for Ace, "hearts.jpg" for hearts suit.
    
    This gets called at startup and whenever /templates/reload is hit.
    TODO: Add template validation to ensure they're the right size/format
    TODO: Maybe add a check to warn if templates look corrupted or wrong
    """
    global rank_templates, suit_templates
    
    rank_templates = {}
    suit_templates = {}
    
    # Load rank templates - these are images of just the rank symbols (A, K, Q, etc.)
    if not os.path.exists(RANK_DIR):
        logger.warning(f"Rank template directory not found: {RANK_DIR}")
    else:
        for filename in os.listdir(RANK_DIR):
            # Support common image formats - JPG, PNG, etc.
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                name = os.path.splitext(filename)[0]  # Get name without extension
                img_path = os.path.join(RANK_DIR, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Load as grayscale for matching
                if img is not None:
                    rank_templates[name] = img
                    logger.debug(f"Loaded rank template: {name}")
                else:
                    logger.warning(f"Failed to load rank template: {img_path}")
    
    # Load suit templates - same process for suits (hearts, spades, etc.)
    if not os.path.exists(SUIT_DIR):
        logger.warning(f"Suit template directory not found: {SUIT_DIR}")
    else:
        for filename in os.listdir(SUIT_DIR):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(SUIT_DIR, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    suit_templates[name] = img
                    logger.debug(f"Loaded suit template: {name}")
                else:
                    logger.warning(f"Failed to load suit template: {img_path}")
    
    logger.info(f"Loaded {len(rank_templates)} rank templates and {len(suit_templates)} suit templates.")
    
    # Warn if templates are missing - recognition won't work without them
    # This is a common mistake when setting up the project
    if len(rank_templates) == 0 or len(suit_templates) == 0:
        logger.error("WARNING: No templates loaded. Card recognition will not work properly.")

load_templates()

class CardResult(BaseModel):
    rank: str
    rank_score: float = Field(ge=0.0, le=1.0, description="Confidence score for rank recognition")
    suit: str
    suit_score: float = Field(ge=0.0, le=1.0, description="Confidence score for suit recognition")

class RecognitionResponse(BaseModel):
    cards: List[CardResult]
    count: int
    message: Optional[str] = None

def preprocess_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Decodes image bytes to OpenCV format.
    
    Handles the conversion from bytes (as received from HTTP request) to
    a numpy array that OpenCV can work with. Pretty straightforward, but
    important to validate at each step - bad images can crash the pipeline.
    
    Returns None if anything goes wrong, so the caller can handle it gracefully.
    """
    try:
        if len(image_bytes) == 0:
            logger.error("Received empty image data")
            return None
            
        # Convert bytes to numpy array, then decode with OpenCV
        # OpenCV can handle JPEG, PNG, etc. automatically
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # Keep color for now, convert to gray later
        
        if img is None:
            logger.error("Failed to decode image - might be corrupted or wrong format")
            return None
            
        if img.size == 0:
            logger.error("Decoded image is empty")
            return None
            
        logger.debug(f"Decoded image with shape: {img.shape}")
        return img
    except Exception as e:
        # Catch any unexpected errors during decoding
        logger.error(f"Error preprocessing image: {e}", exc_info=True)
        return None

def find_cards(img: np.ndarray) -> List[np.ndarray]:
    """
    Finds card contours in the image.
    
    Uses edge detection and contour finding to locate rectangular card shapes.
    The approach:
    1. Convert to grayscale (easier to work with)
    2. Apply Gaussian blur to reduce noise (helps with edge detection)
    3. Threshold to get binary image (OTSU is pretty good at auto-thresholding)
    4. Find contours (connected regions)
    5. Filter for rectangular shapes (4 corners) and minimum area
    
    This works well for cards on a contrasting background. Could be improved
    with adaptive thresholding for varying lighting conditions, but this is
    good enough for most cases.
    
    Returns a list of contours that look like cards (4-sided polygons).
    """
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)  # Reduce noise - helps with edge detection
        # OTSU automatically picks a good threshold value
        _, thresh = cv2.threshold(blur, 120, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Find all contours in the thresholded image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        card_contours = []
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > MIN_CARD_AREA:  # Filter out small noise/artifacts
                peri = cv2.arcLength(cnt, True)
                if peri == 0:
                    continue
                # Approximate contour to polygon - cards should have 4 corners
                # The 0.02 factor controls how much we simplify the contour
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
                if len(approx) == 4:  # Rectangular shape (4 corners = card-like)
                    card_contours.append(approx)
        
        logger.debug(f"Found {len(card_contours)} card contours")
        return card_contours
    except Exception as e:
        logger.error(f"Error finding cards: {e}", exc_info=True)
        return []

def warp_card(img: np.ndarray, contour: np.ndarray) -> Optional[np.ndarray]:
    """
    Warps the perspective of a card contour to a flat, normalized image.
    
    Cards in photos are often at an angle or perspective. This function uses
    perspective transformation to "flatten" the card to a standard size and
    orientation. Makes template matching much more reliable since all cards
    are the same size and orientation.
    
    The trick is correctly ordering the corner points - using sum/diff of
    coordinates to identify top-left, top-right, etc. This is a common
    computer vision technique for perspective correction.
    
    Returns None if the contour doesn't have exactly 4 points (not a valid card).
    """
    try:
        if len(contour) != 4:
            return None
            
        pts = contour.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")

        # Order points: top-left, top-right, bottom-right, bottom-left
        # Top-left has smallest sum (x+y), bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right

        # Top-right has smallest diff (x-y), bottom-left has largest diff
        # This distinguishes between the two remaining corners
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left

        # Destination points for the warped card - normalized rectangle
        dst = np.array([
            [0, 0],
            [CARD_WIDTH - 1, 0],
            [CARD_WIDTH - 1, CARD_HEIGHT - 1],
            [0, CARD_HEIGHT - 1]
        ], dtype="float32")

        # Calculate perspective transform matrix and apply it
        # This is the magic that flattens the card
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (CARD_WIDTH, CARD_HEIGHT))
        return warped
    except Exception as e:
        logger.error(f"Error warping card: {e}", exc_info=True)
        return None

def match_template(roi: np.ndarray, templates: dict, min_score: float = 0.0) -> tuple[str, float]:
    """
    Matches an ROI (region of interest) against a set of templates and returns the best match.
    
    Uses OpenCV's template matching with normalized correlation coefficient.
    Tries all templates and returns the one with the highest score.
    
    Handles size mismatches by scaling templates down if needed. Could also
    scale up, but that usually doesn't work as well (upscaling adds artifacts).
    
    Returns tuple of (best_match_name, best_match_score). Score is between 0 and 1.
    """
    best_name = "Unknown"
    best_score = min_score
    
    if not templates or roi is None or roi.size == 0:
        return best_name, best_score

    try:
        # Convert to grayscale if needed (templates are already grayscale)
        # This ensures we're comparing apples to apples
        if len(roi.shape) == 3:
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            roi_gray = roi.copy()
            
        # Threshold to binary - makes matching more robust to lighting variations
        # This way we're matching shapes, not colors/brightness
        _, roi_thresh = cv2.threshold(roi_gray, 125, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        r_h, r_w = roi_thresh.shape
        
        if r_h == 0 or r_w == 0:
            return best_name, best_score

        # Try matching against each template - find the best match
        for name, template in templates.items():
            if template is None or template.size == 0:
                continue
                
            t_h, t_w = template.shape
            
            # Handle size mismatches - scale template down if it's too large
            # Template must be smaller than ROI for matching to work
            if t_h > r_h or t_w > r_w:
                scale = min(r_h / t_h, r_w / t_w)
                if scale < 0.5:  # Too much scaling loses too much detail, skip it
                    continue
                scaled_template = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                t_h, t_w = scaled_template.shape
            else:
                scaled_template = template

            # Double-check template fits (should always be true after scaling)
            if t_h > r_h or t_w > r_w:
                continue

            try:
                # Normalized correlation coefficient - returns values between -1 and 1
                # Higher is better, 1.0 is perfect match
                # This method is robust to brightness variations
                res = cv2.matchTemplate(roi_thresh, scaled_template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)  # Get the best match score
                
                if max_val > best_score:
                    best_score = max_val
                    best_name = name
            except cv2.error as e:
                # Some templates might fail due to size issues, just skip them
                # Better to skip than crash the whole recognition
                logger.debug(f"Template matching error for {name}: {e}")
                continue
                
        return best_name, best_score
    except Exception as e:
        logger.error(f"Error in template matching: {e}", exc_info=True)
        return best_name, best_score

@app.post("/recognize", response_model=RecognitionResponse)
async def recognize_cards(file: UploadFile = File(...)):
    """
    Receives an image, detects cards, and identifies rank/suit.
    
    Main endpoint for card recognition. The iOS app sends images here.
    Process:
    1. Decode image from bytes
    2. Find card contours (rectangular shapes)
    3. Warp each card to normalized size (perspective correction)
    4. Extract rank/suit regions from corner
    5. Match against templates
    6. Return results with confidence scores
    
    Only returns cards that meet minimum confidence thresholds to filter
    out false positives.
    """
    try:
        # Validate file type
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Expected an image."
            )
        
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty file received")
        
        # Check if templates are loaded
        if len(rank_templates) == 0 or len(suit_templates) == 0:
            logger.warning("Templates not loaded, recognition may fail")
            return RecognitionResponse(
                cards=[],
                count=0,
                message="Warning: Templates not loaded. Please check template directories."
            )
        
        img = preprocess_image(contents)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Failed to decode image. Please ensure the file is a valid image.")
        
        if img.size == 0:
            raise HTTPException(status_code=400, detail="Decoded image is empty")

        contours = find_cards(img)
        
        if len(contours) == 0:
            return RecognitionResponse(
                cards=[],
                count=0,
                message="No cards detected. Try improving lighting or card positioning."
            )
        
        results = []

        # Process each detected card contour
        for i, cnt in enumerate(contours):
            try:
                # Warp the card to a normalized size/orientation
                warped = warp_card(img, cnt)
                
                if warped is None:
                    logger.debug(f"Failed to warp card contour {i}")
                    continue
                
                # Extract corner region for rank/suit detection
                # Standard playing cards have rank/suit in the top-left corner
                # Check bounds first to avoid index errors
                if warped.shape[0] < CORNER_Y + CORNER_H or warped.shape[1] < CORNER_X + CORNER_W:
                    logger.debug(f"Card {i} too small for corner extraction")
                    continue
                    
                corner = warped[CORNER_Y:CORNER_Y+CORNER_H, CORNER_X:CORNER_X+CORNER_W]
                
                if corner.size == 0:
                    continue
                
                # Split corner into rank (top ~45px) and suit (bottom ~40px)
                # These values work for standard cards, might need adjustment for others
                # Using min() to handle edge cases where card is smaller than expected
                rank_roi = corner[0:min(45, corner.shape[0]), :]
                suit_roi = corner[min(45, corner.shape[0]):min(85, corner.shape[0]), :]
                
                if rank_roi.size == 0 or suit_roi.size == 0:
                    continue
                
                # Match against templates - this is where the actual recognition happens
                rank, rank_score = match_template(rank_roi, rank_templates, MIN_RANK_SCORE)
                suit, suit_score = match_template(suit_roi, suit_templates, MIN_SUIT_SCORE)
                
                # Only add cards that meet minimum confidence thresholds
                # This filters out false positives from poor matches
                # Better to miss a card than to give wrong information
                if rank_score >= MIN_RANK_SCORE and suit_score >= MIN_SUIT_SCORE:
                    results.append(CardResult(
                        rank=rank,
                        rank_score=float(rank_score),
                        suit=suit,
                        suit_score=float(suit_score)
                    ))
                else:
                    logger.debug(f"Card {i} rejected: rank_score={rank_score:.2f}, suit_score={suit_score:.2f}")
            except Exception as e:
                # If one card fails, continue processing others
                logger.error(f"Error processing card contour {i}: {e}", exc_info=True)
                continue

        message = None
        if len(results) == 0 and len(contours) > 0:
            message = "Cards detected but recognition confidence too low. Try better lighting or angle."

        return RecognitionResponse(cards=results, count=len(results), message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in recognize_cards: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
def health_check():
    """
    Health check endpoint.
    
    Useful for monitoring and debugging. Shows if templates are loaded correctly.
    Hit this endpoint to verify the server is running and templates are available.
    """
    template_status = {
        "rank_templates": len(rank_templates),
        "suit_templates": len(suit_templates),
        "templates_loaded": len(rank_templates) > 0 and len(suit_templates) > 0
    }
    return {
        "status": "ok",
        "service": "card_cv_server",
        "version": "1.0.0",
        "templates": template_status
    }

@app.get("/templates/reload")
def reload_templates():
    """
    Reload templates from disk.
    
    Useful when you update template images without restarting the server.
    Saves time during development - just update the template files and hit this endpoint.
    
    Returns the count of loaded templates so you can verify everything loaded correctly.
    """
    try:
        load_templates()
        return {
            "status": "success",
            "rank_templates": len(rank_templates),
            "suit_templates": len(suit_templates)
        }
    except Exception as e:
        logger.error(f"Error reloading templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reload templates: {str(e)}")

if __name__ == "__main__":
    # Run the server - defaults to port 8000
    # Can override with PORT and HOST environment variables
    # Useful for running multiple instances or custom configurations
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")
    logger.info("Make sure templates are loaded before sending recognition requests!")
    uvicorn.run(app, host=host, port=port, log_level="info")
