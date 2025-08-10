"""
Screen configuration helper utility
"""
import tkinter as tk
from typing import Dict, Any


def detect_screen_setup() -> Dict[str, Any]:
    """Detect current screen setup and display information using Windows API"""
    try:
        import ctypes
        import ctypes.wintypes
        
        # Windows API constants
        SM_CMONITORS = 80
        
        # Get number of monitors
        num_monitors = ctypes.windll.user32.GetSystemMetrics(SM_CMONITORS)
        print(f"Detected screen setup:")
        print(f"Number of monitors: {num_monitors}")
        
        if num_monitors < 2:
            print("Single monitor setup detected")
            # Use tkinter for single monitor
            root = tk.Tk()
            root.withdraw()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            
            left_half_config = {
                'x': 0,
                'y': 0,
                'width': screen_width // 2,
                'height': screen_height
            }
            
            print(f"Primary monitor: {screen_width}x{screen_height}")
            print(f"Left half configuration: {left_half_config}")
            
            return {
                'monitors': [{'width': screen_width, 'height': screen_height, 'left': 0, 'top': 0}],
                'left_half': left_half_config
            }
        
        # Multiple monitors - get detailed info
        monitors = []
        
        def enum_display_monitors_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            monitors.append({
                'handle': hMonitor,
                'left': lprcMonitor.contents.left,
                'top': lprcMonitor.contents.top,
                'right': lprcMonitor.contents.right,
                'bottom': lprcMonitor.contents.bottom,
                'width': lprcMonitor.contents.right - lprcMonitor.contents.left,
                'height': lprcMonitor.contents.bottom - lprcMonitor.contents.top
            })
            return True
        
        # Define the callback function type
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.wintypes.HMONITOR,
            ctypes.wintypes.HDC,
            ctypes.POINTER(ctypes.wintypes.RECT),
            ctypes.wintypes.LPARAM
        )
        
        # Enumerate all monitors
        ctypes.windll.user32.EnumDisplayMonitors(
            None, None, MonitorEnumProc(enum_display_monitors_proc), 0
        )
        
        # Sort monitors by left position
        monitors.sort(key=lambda m: m['left'])
        
        print(f"Multiple monitors detected:")
        for i, monitor in enumerate(monitors):
            print(f"  Monitor {i+1}: {monitor['width']}x{monitor['height']} at ({monitor['left']}, {monitor['top']})")
        
        # Find secondary monitor
        secondary_monitor = None
        for monitor in monitors:
            if monitor['left'] != 0 or monitor['top'] != 0:
                secondary_monitor = monitor
                break
        
        if secondary_monitor is None and len(monitors) > 1:
            secondary_monitor = monitors[1]
        
        if secondary_monitor is None:
            secondary_monitor = monitors[0]
        
        # Calculate left half of secondary monitor
        left_half_config = {
            'x': secondary_monitor['left'],
            'y': secondary_monitor['top'],
            'width': secondary_monitor['width'] // 2,
            'height': secondary_monitor['height']
        }
        
        print(f"Secondary monitor selected: {secondary_monitor['width']}x{secondary_monitor['height']} at ({secondary_monitor['left']}, {secondary_monitor['top']})")
        print(f"Left half configuration: {left_half_config}")
        
        return {
            'monitors': monitors,
            'secondary_monitor': secondary_monitor,
            'left_half': left_half_config
        }
        
    except Exception as e:
        print(f"Error detecting screen setup with Windows API: {e}")
        print("Falling back to tkinter method...")
        
        # Fallback to tkinter
        try:
            root = tk.Tk()
            root.withdraw()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            
            if screen_width > 2000:
                left_half_config = {
                    'x': 1920,
                    'y': 0,
                    'width': (screen_width - 1920) // 2,
                    'height': screen_height
                }
            else:
                left_half_config = {
                    'x': 0,
                    'y': 0,
                    'width': screen_width // 2,
                    'height': screen_height
                }
            
            print(f"Fallback detection - Total: {screen_width}x{screen_height}")
            print(f"Left half configuration: {left_half_config}")
            
            return {
                'total_width': screen_width,
                'total_height': screen_height,
                'left_half': left_half_config
            }
            
        except Exception as e2:
            print(f"Fallback method also failed: {e2}")
            return None


def create_custom_config(x: int, y: int, width: int, height: int) -> Dict[str, int]:
    """Create a custom window configuration"""
    config = {
        'x': x,
        'y': y,
        'width': width,
        'height': height
    }
    print(f"Custom configuration created: {config}")
    return config


def test_window_position(x: int, y: int, width: int, height: int) -> None:
    """Test window position by opening a test window"""
    try:
        root = tk.Tk()
        root.title("Test Window Position")
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        label = tk.Label(root, text=f"Test Window\nPosition: ({x}, {y})\nSize: {width}x{height}", 
                        font=("Arial", 16), pady=20)
        label.pack(expand=True)
        
        close_button = tk.Button(root, text="Close", command=root.destroy, 
                               font=("Arial", 12), pady=10)
        close_button.pack()
        
        print(f"Test window opened at position ({x}, {y}) with size {width}x{height}")
        print("Close the test window to continue...")
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error creating test window: {e}")


if __name__ == "__main__":
    print("=== Screen Configuration Helper ===")
    print()
    
    # Detect current setup
    setup = detect_screen_setup()
    
    if setup:
        print("\n=== Testing left half position ===")
        config = setup['left_half']
        response = input(f"Test window at left half position? (y/n): ")
        
        if response.lower() == 'y':
            test_window_position(config['x'], config['y'], config['width'], config['height'])
        
        print("\n=== Custom Configuration ===")
        print("You can customize the window position in config.py")
        print("Update the WINDOW_POSITION dictionary with your preferred values:")
        print(f"WINDOW_POSITION = {config}")