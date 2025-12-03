# Template Instructions

To enable card recognition, you must add template images to the `ranks` and `suits` directories.

## Quick Summary

**You need 17 template images:**

### Ranks (13 images)
Place in `ranks/` directory:
- A.jpg, 2.jpg, 3.jpg, 4.jpg, 5.jpg, 6.jpg, 7.jpg, 8.jpg, 9.jpg, 10.jpg, J.jpg, Q.jpg, K.jpg

### Suits (4 images)  
Place in `suits/` directory:
- hearts.jpg, diamonds.jpg, clubs.jpg, spades.jpg

## What Are Template Images?

Template images are **reference pictures** of the card symbols that the system uses to identify cards. They should be cropped images showing just the rank or suit symbol from the top-left corner of a playing card.

## How to Create Them

1. **Take photos** of your playing cards (focus on the top-left corner)
2. **Crop** to show just the rank or suit symbol
3. **Save** with the correct filename (e.g., `A.jpg`, `hearts.jpg`)
4. **Place** in the appropriate directory

## Detailed Guide

See `TEMPLATE_GUIDE.md` for:
- Step-by-step instructions
- Image requirements and tips
- Troubleshooting
- Example workflow

## File Format

- Supported: .jpg, .jpeg, .png
- Recommended: White/light background
- Size: Any size (system scales automatically)
- Quality: Sharp, well-lit images work best

## Quick Test

After adding templates, start the server and check:
```bash
curl http://localhost:8000/
```

Should show template counts like:
```json
{
  "templates": {
    "rank_templates": 13,
    "suit_templates": 4
  }
}
```
