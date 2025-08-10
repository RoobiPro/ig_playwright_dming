"""
Simple position calibration script
Opens browser, lets you position it manually, then captures exact values
"""
from playwright.sync_api import sync_playwright
import time


def main():
    """Main calibration function"""
    print("🎯 Window Position Calibration")
    print("=" * 50)
    print("This script will:")
    print("1. Open a browser window")
    print("2. Let you manually position and resize it")
    print("3. Capture the exact position and size values")
    print("4. Display them for you to copy")
    print("=" * 50)
    print()
    
    with sync_playwright() as playwright:
        # Launch browser with minimal configuration
        browser = playwright.chromium.launch(
            headless=False,
            args=[
                "--disable-web-security",
                "--disable-features=TranslateUI",
                "--no-first-run",
                "--disable-infobars"
            ]
        )
        
        context = browser.new_context()
        page = context.new_page()
        
        # Navigate to a simple page
        print("📱 Opening browser and navigating to Google...")
        page.goto("https://www.google.com")
        page.wait_for_timeout(2000)
        
        # Get initial position for reference
        initial_pos = page.evaluate("""
            ({
                x: window.screenX,
                y: window.screenY,
                width: window.outerWidth,
                height: window.outerHeight
            })
        """)
        
        print(f"📍 Initial position: x={initial_pos['x']}, y={initial_pos['y']}, "
              f"size={initial_pos['width']}x{initial_pos['height']}")
        print()
        
        # Instructions for manual positioning
        print("🔧 MANUAL POSITIONING:")
        print("→ Move the browser window to your secondary screen")
        print("→ Position it on the LEFT HALF of your secondary screen")
        print("→ Resize it to fill exactly the left half")
        print("→ Make sure it's positioned perfectly where you want it")
        print()
        print("⏳ When you're satisfied with the position, press Enter...")
        
        # Wait for user to position window
        input()
        
        # Capture the final position
        final_pos = page.evaluate("""
            ({
                x: window.screenX,
                y: window.screenY,
                width: window.outerWidth,
                height: window.outerHeight,
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
                screenWidth: window.screen.width,
                screenHeight: window.screen.height
            })
        """)
        
        # Display results
        print()
        print("✅ CAPTURED WINDOW POSITION:")
        print("=" * 50)
        print(f"X Position: {final_pos['x']}")
        print(f"Y Position: {final_pos['y']}")
        print(f"Width: {final_pos['width']}")
        print(f"Height: {final_pos['height']}")
        print(f"Content Width: {final_pos['innerWidth']}")
        print(f"Content Height: {final_pos['innerHeight']}")
        print(f"Screen Dimensions: {final_pos['screenWidth']}x{final_pos['screenHeight']}")
        print("=" * 50)
        print()
        
        # Display configuration to copy
        print("📋 CONFIGURATION VALUES:")
        print("Copy these values and provide them back:")
        print()
        print("```")
        print("CALIBRATED_WINDOW_POSITION = {")
        print(f"    'x': {final_pos['x']},")
        print(f"    'y': {final_pos['y']},")
        print(f"    'width': {final_pos['width']},")
        print(f"    'height': {final_pos['height']}")
        print("}")
        print("```")
        print()
        
        # Additional info
        print("📊 ADDITIONAL INFO:")
        print(f"Window right edge: {final_pos['x'] + final_pos['width']}")
        print(f"Window bottom edge: {final_pos['y'] + final_pos['height']}")
        print(f"Content area: {final_pos['innerWidth']}x{final_pos['innerHeight']}")
        print()
        
        # Wait before closing
        input("Press Enter to close the browser...")
        browser.close()
        
        print()
        print("🎉 Calibration complete!")
        print("Please copy the CALIBRATED_WINDOW_POSITION values above")
        print("and provide them back to update the script.")


if __name__ == "__main__":
    main()