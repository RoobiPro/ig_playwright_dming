"""
Simple window position capture script
"""
from playwright.sync_api import sync_playwright


def main():
    print("Window Position Capture")
    print("=" * 30)
    print("1. Browser will open")
    print("2. Position and resize it manually")
    print("3. Press Enter to capture position")
    print("4. Copy the values shown")
    print()
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://www.google.com")
        page.wait_for_timeout(1000)
        
        print("Browser opened. Position it where you want, then press Enter...")
        input()
        
        # Capture position
        pos = page.evaluate("""
            ({
                x: window.screenX,
                y: window.screenY,
                width: window.outerWidth,
                height: window.outerHeight
            })
        """)
        
        print()
        print("CAPTURED POSITION:")
        print(f"X: {pos['x']}")
        print(f"Y: {pos['y']}")
        print(f"Width: {pos['width']}")
        print(f"Height: {pos['height']}")
        print()
        print("Copy these values:")
        print(f"x={pos['x']}, y={pos['y']}, width={pos['width']}, height={pos['height']}")
        
        input("Press Enter to close...")
        browser.close()


if __name__ == "__main__":
    main()