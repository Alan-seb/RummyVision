# Template Images Guide

## What Are Template Images?

Template images are **reference pictures** of the card symbols (ranks and suits) that the computer vision system uses to identify cards. Think of them as "answer keys" - when the system sees a card, it compares the rank and suit symbols against these templates to figure out what card it is.

## Why Do You Need Them?

The card recognition system works by:
1. Detecting card shapes in your photo
2. Extracting the rank and suit symbols from the card corner
3. **Matching those symbols against your template images**
4. Identifying which card it is based on the best match

Without template images, the system has nothing to compare against, so it can't identify cards!

## What You Need to Create

You need **17 template images total**:

### Rank Templates (13 images)
- `A.jpg` - Ace
- `2.jpg` through `10.jpg` - Number cards
- `J.jpg` - Jack
- `Q.jpg` - Queen  
- `K.jpg` - King

### Suit Templates (4 images)
- `hearts.jpg` - Hearts suit symbol
- `diamonds.jpg` - Diamonds suit symbol
- `clubs.jpg` - Clubs suit symbol
- `spades.jpg` - Spades suit symbol

## How to Create Template Images

### Method 1: Using Your iPhone Camera (Recommended)

1. **Take photos of your actual playing cards:**
   - Place a card on a plain, well-lit surface (white or dark background works)
   - Use good, even lighting
   - Take a close-up photo of the **top-left corner** of the card where the rank and suit are

2. **Crop the images:**
   - For **rank templates**: Crop to show just the rank symbol (A, 2, 3, etc.)
   - For **suit templates**: Crop to show just the suit symbol (♥, ♦, ♣, ♠)
   - Keep some white space around the symbol

3. **Save with correct names:**
   - Rank images: `A.jpg`, `2.jpg`, `3.jpg`, etc.
   - Suit images: `hearts.jpg`, `diamonds.jpg`, `clubs.jpg`, `spades.jpg`

### Method 2: Using Image Editing Software

1. **Take a photo of a full card** with good lighting
2. **Open in image editor** (Photoshop, GIMP, Preview, etc.)
3. **Crop the corner area:**
   - For ranks: Crop the top portion showing the rank
   - For suits: Crop the bottom portion showing the suit
4. **Save as JPG or PNG**

### Method 3: Using Online Card Images

1. Find high-quality card images online
2. Download and crop the corner symbols
3. Save with the correct filenames

## Image Requirements

### Size
- **No specific size required** - the system will scale automatically
- Recommended: 50-200 pixels wide/tall
- Larger is generally better (up to a point)

### Format
- **File formats**: `.jpg`, `.jpeg`, or `.png`
- **Color**: Color images are fine (system converts to grayscale)
- **Background**: White or light background works best

### Quality Tips
- ✅ **Good lighting** - no shadows on the symbols
- ✅ **Sharp focus** - symbols should be clear, not blurry
- ✅ **Consistent style** - use the same deck/card design for all templates
- ✅ **Plain background** - white or light background around the symbol
- ❌ Avoid shadows, glare, or reflections
- ❌ Avoid different card designs (stick to one deck)

## File Structure

Your templates should be organized like this:

```
server/
  templates/
    ranks/
      A.jpg
      2.jpg
      3.jpg
      4.jpg
      5.jpg
      6.jpg
      7.jpg
      8.jpg
      9.jpg
      10.jpg
      J.jpg
      Q.jpg
      K.jpg
    suits/
      hearts.jpg
      diamonds.jpg
      clubs.jpg
      spades.jpg
```

## Example Workflow

### Step 1: Prepare Your Cards
- Get a standard deck of playing cards
- Choose a well-lit area with a plain background

### Step 2: Create Rank Templates
1. Take a photo of the Ace card (focus on top-left corner)
2. Crop to show just the "A" symbol
3. Save as `A.jpg` in `server/templates/ranks/`
4. Repeat for 2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K

### Step 3: Create Suit Templates
1. Take a photo of any card showing hearts
2. Crop to show just the ♥ symbol
3. Save as `hearts.jpg` in `server/templates/suits/`
4. Repeat for diamonds, clubs, spades

### Step 4: Verify
1. Start the CV server: `python3 card_cv_server.py`
2. Check the logs - it should say:
   ```
   Loaded 13 rank templates and 4 suit templates.
   ```
3. Visit `http://localhost:8000/` to verify template count

## Quick Test

After adding templates, test with a simple image:

```bash
# Using the test client (if you have a test image)
cd utils
python3 test_client.py path/to/card_image.jpg
```

## Troubleshooting

### "No templates loaded" error
- Check file names match exactly (case-sensitive on some systems)
- Verify files are in correct directories
- Check file extensions (.jpg, .jpeg, or .png)
- Ensure images can be opened/viewed normally

### Low recognition accuracy
- Improve template image quality (better lighting, sharper focus)
- Use templates from the same deck design as your cards
- Ensure consistent background (white/light)
- Try adjusting `MIN_RANK_SCORE` and `MIN_SUIT_SCORE` in server config

### Templates not matching
- Make sure templates are from the same card deck design
- Check that you're cropping the correct corner (top-left)
- Verify the card design matches (some decks have different styles)

## Pro Tips

1. **Use the same deck**: Templates should match your actual cards' design
2. **Good lighting**: Take template photos in the same lighting conditions you'll use
3. **Multiple angles**: You can create templates for different card orientations if needed
4. **Test and refine**: After creating templates, test recognition and adjust if needed
5. **Backup**: Keep your template images backed up - they're important!

## Need Help?

If you're having trouble creating templates:
1. Check the server logs for template loading messages
2. Verify file names and locations
3. Test with a simple card photo first
4. Adjust confidence thresholds if recognition is too strict/loose

Good luck! 🎴

