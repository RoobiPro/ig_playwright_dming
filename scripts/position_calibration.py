"""
Position calibration utility
Opens browser, allows manual positioning, then captures exact values
"""
from playwright.sync_api import sync_playwright
import time
import json
import os


def capture_window_position():
    """Capture window position after manual adjustment"""
    print("=== Window Position Calibration ===")
    print("This script will:")
    print("1. Open a browser window")
    print("2. Let you manually position and resize it")
    print("3. Capture the exact position and size values")
    print("4. Save them for use in the automation")
    print()
    
    with sync_playwright() as playwright:
        # Launch browser with minimal arguments
        browser = playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-web-security",
                "--disable-features=TranslateUI",
                "--no-first-run"
            ]
        )
        
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate to a simple page
        print("Opening browser and navigating to Google...")
        page.goto("https://www.google.com")
        
        # Wait for page to load
        page.wait_for_timeout(2000)
        
        # Get initial position
        initial_pos = page.evaluate("""
            ({
                x: window.screenX,
                y: window.screenY,
                width: window.outerWidth,
                height: window.outerHeight,
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight
            })
        """)
        
        print(f"Initial window position: {initial_pos}")
        print()
        print("=" * 60)
        print("MANUAL POSITIONING INSTRUCTIONS:")
        print("=" * 60)
        print("1. Move the browser window to your desired position")
        print("2. Resize it to your desired size")
        print("3. Make sure it's positioned exactly where you want it")
        print("4. Press Enter in this terminal when you're done")
        print("=" * 60)
        print()
        
        # Wait for user confirmation
        input("Press Enter when you have positioned the window correctly...")
        
        # Capture final position
        final_pos = page.evaluate("""
            ({
                x: window.screenX,
                y: window.screenY,
                width: window.outerWidth,
                height: window.outerHeight,
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
                screenWidth: window.screen.width,
                screenHeight: window.screen.height,
                availWidth: window.screen.availWidth,
                availHeight: window.screen.availHeight
            })
        """)
        
        print("\n" + "=" * 60)
        print("CAPTURED WINDOW POSITION VALUES:")
        print("=" * 60)
        print(f"Window X Position: {final_pos['x']}")
        print(f"Window Y Position: {final_pos['y']}")
        print(f"Window Width: {final_pos['width']}")
        print(f"Window Height: {final_pos['height']}")
        print(f"Content Width: {final_pos['innerWidth']}")
        print(f"Content Height: {final_pos['innerHeight']}")
        print(f"Screen Width: {final_pos['screenWidth']}")
        print(f"Screen Height: {final_pos['screenHeight']}")
        print("=" * 60)
        
        # Calculate some useful derived values
        print("\nDERIVED VALUES:")
        print(f"Window right edge: {final_pos['x'] + final_pos['width']}")
        print(f"Window bottom edge: {final_pos['y'] + final_pos['height']}")
        print(f"Window center X: {final_pos['x'] + final_pos['width'] // 2}")
        print(f"Window center Y: {final_pos['y'] + final_pos['height'] // 2}")
        
        # Save to config file
        config_data = {
            "calibrated_position": {
                "x": final_pos['x'],
                "y": final_pos['y'],
                "width": final_pos['width'],
                "height": final_pos['height']
            },
            "screen_info": {
                "screen_width": final_pos['screenWidth'],
                "screen_height": final_pos['screenHeight'],
                "avail_width": final_pos['availWidth'],
                "avail_height": final_pos['availHeight']
            },
            "content_area": {
                "inner_width": final_pos['innerWidth'],
                "inner_height": final_pos['innerHeight']
            },
            "timestamp": time.time()
        }
        
        # Save to file
        config_file = "calibrated_window_position.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"\nPosition data saved to: {config_file}")
        
        print("\n" + "=" * 60)
        print("CONFIGURATION VALUES TO COPY:")
        print("=" * 60)
        print("Copy these values and provide them back:")
        print()
        print("WINDOW_POSITION = {")
        print(f"    'x': {final_pos['x']},")
        print(f"    'y': {final_pos['y']},")
        print(f"    'width': {final_pos['width']},")
        print(f"    'height': {final_pos['height']}")
        print("}")
        print()
        print("VIEWPORT_SIZE = {")
        print(f"    'width': {final_pos['innerWidth']},")
        print(f"    'height': {final_pos['innerHeight']}")
        print("}")
        print("=" * 60)
        
        # Wait for final confirmation before closing
        input("\nPress Enter to close the browser...")
        
        browser.close()
        
        return config_data


def test_calibrated_position():
    """Test the calibrated position"""
    try:
        with open("calibrated_window_position.json", 'r') as f:
            config_data = json.load(f)
        
        print("Testing calibrated position...")
        
        with sync_playwright() as playwright:
            pos = config_data["calibrated_position"]
            
            browser = playwright.chromium.launch(
                headless=False,
                args=[
                    f"--window-position={pos['x']},{pos['y']}",
                    f"--window-size={pos['width']},{pos['height']}",
                    "--disable-web-security",
                    "--no-first-run"
                ]
            )
            
            context = browser.new_context(
                no_viewport=True  # Dynamic viewport
            )
            page = context.new_page()
            
            page.goto("https://www.google.com")
            page.wait_for_timeout(2000)
            
            # Fine-tune positioning and set zoom
            page.evaluate(f"""
                window.moveTo({pos['x']}, {pos['y']});
                window.resizeTo({pos['width']}, {pos['height']});
                document.body.style.transform = 'scale(0.8)';
                document.body.style.transformOrigin = 'top left';
                document.body.style.width = '125%';
                document.body.style.height = '125%';
            """)
            
            # Verify final position
            actual_pos = page.evaluate("""
                ({
                    x: window.screenX,
                    y: window.screenY,
                    width: window.outerWidth,
                    height: window.outerHeight
                })
            """)
            
            print(f"Intended position: {pos}")
            print(f"Actual position: {actual_pos}")
            
            input("Press Enter to close test browser...")
            browser.close()
            
    except FileNotFoundError:
        print("No calibrated position found. Run capture_window_position() first.")
    except Exception as e:
        print(f"Error testing position: {e}")


if __name__ == "__main__":
    print("Window Position Calibration Tool")
    print("================================")
    print()
    print("Choose an option:")
    print("1. Capture new window position")
    print("2. Test existing calibrated position")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        capture_window_position()
    elif choice == "2":
        test_calibrated_position()
    else:
        print("Invalid choice. Please run again and choose 1 or 2.")