"""
Test window positioning utility
"""
from .instagram_automation import InstagramAutomation
import time


def test_window_positioning():
    """Test window positioning functionality"""
    print("=== Testing Window Positioning ===")
    
    automation = InstagramAutomation(headless=False)
    
    try:
        # Start browser
        automation.start_browser()
        
        # Navigate to a simple page for testing
        automation.page.goto("https://www.google.com")
        
        print("\n1. Initial window position:")
        initial_pos = automation.get_window_position()
        print(f"   Position: {initial_pos}")
        
        # Test alignment to left half
        print("\n2. Aligning to left half of secondary screen...")
        automation.align_window_to_left_half()
        
        time.sleep(2)
        
        print("\n3. Final window position:")
        final_pos = automation.get_window_position()
        print(f"   Position: {final_pos}")
        
        # Test centering
        print("\n4. Centering window on secondary screen...")
        automation.center_window_on_secondary_screen()
        
        time.sleep(2)
        
        print("\n5. Centered window position:")
        centered_pos = automation.get_window_position()
        print(f"   Position: {centered_pos}")
        
        # Back to left half
        print("\n6. Back to left half...")
        automation.align_window_to_left_half()
        
        time.sleep(2)
        
        print("\n7. Final left half position:")
        final_left_pos = automation.get_window_position()
        print(f"   Position: {final_left_pos}")
        
        input("\nPress Enter to close browser...")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        automation.close_browser()


if __name__ == "__main__":
    test_window_positioning()