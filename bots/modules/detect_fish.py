import cv2
import numpy as np
import pyautogui
from pathlib import Path
import time

def load_template(template_path):
    """Load the template image."""
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template

def detect_template(screenshot, template, threshold=0.8):
    """
    Detect template in screenshot using template matching.
    
    Args:
        screenshot: The screenshot image (BGR format)
        template: The template image to find (BGR format)
        threshold: Matching threshold (0.0 to 1.0), higher = more strict
    
    Returns:
        dict with 'found', 'x', 'y', 'confidence', 'width', 'height', 'all_matches'
    """
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    # Get template dimensions
    template_h, template_w = template_gray.shape
    
    # Perform template matching
    result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    
    # Find all locations above threshold
    locations = np.where(result >= threshold)
    
    # Get the best match location
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    all_matches = []
    for y, x in zip(locations[0], locations[1]):
        all_matches.append({
            'x': x,
            'y': y,
            'confidence': result[y, x]
        })
    
    if len(all_matches) > 0:
        # Sort by confidence
        all_matches.sort(key=lambda m: m['confidence'], reverse=True)
        best = all_matches[0]
        
        return {
            'found': True,
            'x': best['x'],
            'y': best['y'],
            'confidence': best['confidence'],
            'width': template_w,
            'height': template_h,
            'center_x': best['x'] + template_w // 2,
            'center_y': best['y'] + template_h // 2,
            'all_matches': all_matches
        }
    
    return {
        'found': False,
        'confidence': max_val,
        'all_matches': all_matches
    }

def detect_fish(template_path="templates/fish.png", threshold=0.8, screenshot=None, debug=False):
    """
    Detect fish template in the game screen.
    
    Args:
        template_path: Path to the fish template image
        threshold: Matching confidence threshold (default 0.8)
        screenshot: Optional pre-captured screenshot (numpy array)
        debug: Save debug screenshots
    
    Returns:
        Detection result dict
    """
    # Check if template exists
    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = Path.cwd() / template_path
    
    if not template_file.exists():
        alternatives = [
            template_path,
            "templates/fish.png",
            "./templates/fish.png",
            "../templates/fish.png"
        ]
        for alt in alternatives:
            if Path(alt).exists():
                template_file = Path(alt)
                break
        
        if not template_file.exists():
            return {
                'found': False,
                'error': f"Template not found: {template_path}",
                'searched_paths': alternatives
            }
    
    try:
        # Load template
        template = load_template(str(template_file))
        print(f"Loaded template: {template_file} ({template.shape[1]}x{template.shape[0]})")
        
        # Show template preview
        cv2.imshow("Template", template)
        cv2.waitKey(1000)
        cv2.destroyAllWindows()
        
        # Take screenshot if not provided
        if screenshot is None:
            print("Taking screenshot of entire screen...")
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        print(f"Screenshot size: {screenshot.shape[1]}x{screenshot.shape[0]}")
        
        # Save debug screenshot
        if debug:
            debug_path = f"debug_screenshot_{int(time.time())}.png"
            cv2.imwrite(debug_path, screenshot)
            print(f"Debug screenshot saved: {debug_path}")
        
        # Detect template
        print(f"Searching for template (threshold: {threshold})...")
        result = detect_template(screenshot, template, threshold)
        
        # Show result on screenshot
        if result['found']:
            # Draw rectangle around best match
            img_with_result = screenshot.copy()
            cv2.rectangle(
                img_with_result,
                (result['x'], result['y']),
                (result['x'] + result['width'], result['y'] + result['height']),
                (0, 255, 0), 2
            )
            cv2.circle(img_with_result, (result['center_x'], result['center_y']), 5, (0, 0, 255), -1)
            
            # Draw all other matches
            for match in result['all_matches'][1:]:
                cv2.rectangle(
                    img_with_result,
                    (match['x'], match['y']),
                    (match['x'] + result['width'], match['y'] + result['height']),
                    (255, 0, 0), 1
                )
            
            cv2.imshow("Detection Result", img_with_result)
            cv2.waitKey(2000)
            cv2.destroyAllWindows()
            
            # Save result
            if debug:
                cv2.imwrite("debug_result.png", img_with_result)
        
        return result
        
    except Exception as e:
        return {'found': False, 'error': str(e)}

def click_fish(template_path="templates/fish.png", threshold=0.8, screenshot=None):
    """
    Detect and click on the fish template.
    
    Returns:
        True if clicked, False if not found
    """
    result = detect_fish(template_path, threshold, screenshot)
    
    if result['found']:
        center_x = result['center_x']
        center_y = result['center_y']
        confidence = result['confidence']
        
        print(f"Found fish at ({center_x}, {center_y}) with confidence {confidence:.2%}")
        print(f"Clicking on the fish...")
        
        pyautogui.click(center_x, center_y)
        
        return True
    
    else:
        print("Fish not found!")
        if 'confidence' in result:
            print(f"Best match confidence: {result['confidence']:.2%}")
        return False

if __name__ == "__main__":
    import sys
    
    template = "templates/fish.png"
    threshold = 0.8
    debug = False
    
    if len(sys.argv) > 1:
        template = sys.argv[1]
    if len(sys.argv) > 2:
        threshold = float(sys.argv[2])
    if "--debug" in sys.argv:
        debug = True
    
    print("=" * 50)
    print("Fish Detection Script")
    print("=" * 50)
    print(f"Template: {template}")
    print(f"Threshold: {threshold}")
    print(f"Debug: {debug}")
    print()
    
    result = detect_fish(template, threshold, debug=debug)
    
    print()
    print("=" * 50)
    print("Result:")
    print("=" * 50)
    
    if result['found']:
        print(f"✓ Fish detected!")
        print(f"  Position: ({result['x']}, {result['y']})")
        print(f"  Size: {result['width']}x{result['height']}")
        print(f"  Center: ({result['center_x']}, {result['center_y']})")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Total matches: {len(result['all_matches'])}")
    else:
        print("✗ Fish not detected")
        if 'error' in result:
            print(f"  Error: {result['error']}")
        if 'confidence' in result:
            print(f"  Best match confidence: {result['confidence']:.2%}")
