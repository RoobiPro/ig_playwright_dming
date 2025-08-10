"""
Test the calibrated window position
"""
from .instagram_automation import InstagramAutomation
from . import config
import time


def test_calibrated_position():
    """Test the calibrated window position"""
    print("🧪 Testing Calibrated Window Position")
    print("=" * 50)
    
    # Show the calibrated values
    pos = config.get_calibrated_position()
    print(f"📍 Calibrated position: x={pos['x']}, y={pos['y']}")
    print(f"📏 Calibrated size: {pos['width']}x{pos['height']}")
    print()
    
    automation = InstagramAutomation(headless=False)
    
    try:
        # Start browser
        print("🌐 Starting browser...")
        automation.start_browser()
        
        # Navigate to Google for testing
        print("🔗 Navigating to Google...")
        automation.page.goto("https://www.google.com")
        automation.page.wait_for_timeout(2000)
        
        # Test calibrated positioning
        print("🎯 Applying calibrated position...")
        automation.align_window_to_calibrated_position()
        
        # Wait and verify
        time.sleep(2)
        
        print("✅ Position test complete!")
        print()
        print("🔍 Verify the browser window is positioned exactly where you manually set it.")
        print("The window should be at the exact position and size you calibrated.")
        print()
        
        # Test dynamic positioning for comparison
        choice = input("Would you like to test dynamic positioning for comparison? (y/n): ").lower()
        if choice == 'y':
            print("\n🔄 Testing dynamic positioning...")
            automation.align_window_to_left_half()
            time.sleep(2)
            
            print("📊 Dynamic positioning applied.")
            print("Notice the difference? The calibrated position should be more accurate.")
            print()
            
            # Switch back to calibrated
            print("🔄 Switching back to calibrated position...")
            automation.align_window_to_calibrated_position()
            time.sleep(2)
        
        input("\nPress Enter to close browser...")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        automation.close_browser()


def show_position_info():
    """Show detailed information about the calibrated position"""
    print("📊 Calibrated Position Information")
    print("=" * 50)
    
    pos = config.get_calibrated_position()
    
    print(f"X Position: {pos['x']}")
    print(f"Y Position: {pos['y']}")
    print(f"Width: {pos['width']}")
    print(f"Height: {pos['height']}")
    print()
    
    print("Calculated edges:")
    print(f"Right edge: {pos['x'] + pos['width']}")
    print(f"Bottom edge: {pos['y'] + pos['height']}")
    print(f"Center X: {pos['x'] + pos['width'] // 2}")
    print(f"Center Y: {pos['y'] + pos['height'] // 2}")
    print()
    
    # Show dynamic comparison
    print("🔍 Dynamic detection comparison:")
    try:
        dynamic_pos = config.get_dynamic_screen_configuration()
        print(f"Dynamic position: x={dynamic_pos['x']}, y={dynamic_pos['y']}")
        print(f"Dynamic size: {dynamic_pos['width']}x{dynamic_pos['height']}")
        print()
        
        print("Differences:")
        print(f"X difference: {pos['x'] - dynamic_pos['x']}")
        print(f"Y difference: {pos['y'] - dynamic_pos['y']}")
        print(f"Width difference: {pos['width'] - dynamic_pos['width']}")
        print(f"Height difference: {pos['height'] - dynamic_pos['height']}")
        
    except Exception as e:
        print(f"Could not get dynamic position: {e}")


if __name__ == "__main__":
    print("Calibrated Position Test")
    print("=" * 30)
    print("1. Test calibrated position")
    print("2. Show position information")
    print()
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        test_calibrated_position()
    elif choice == "2":
        show_position_info()
    else:
        print("Invalid choice")