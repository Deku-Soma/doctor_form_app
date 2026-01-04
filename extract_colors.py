import sys
from PIL import Image
from collections import Counter

def get_dominant_colors(image_path, num_colors=5):
    try:
        image = Image.open(image_path)
        image = image.convert('RGB')
        # Resize for speed
        image = image.resize((150, 150))
        
        # Get colors
        pixels = list(image.getdata())
        counts = Counter(pixels)
        
        # Sort by count
        sorted_colors = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"Top {num_colors} colors found:")
        for color, count in sorted_colors[:num_colors]:
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
            print(f"RGB: {color} - Hex: {hex_color} - Count: {count}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_colors.py <image_path>")
        sys.exit(1)
    
    get_dominant_colors(sys.argv[1])
