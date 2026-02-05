import psutil
import win32gui
import win32process
import win32ui
import win32con
from ctypes import windll
import cv2
import numpy as np
import win32ui
from ctypes import windll

def find_fivem_windows():
    """Find all FiveM-related windows."""
    windows = []
    
    def enum_callback(hwnd, windows):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            proc_name = process.name().lower()
            title = win32gui.GetWindowText(hwnd)
            
            # Check for FiveM processes
            if proc_name in ["fivem.exe", "fivem_gtaprocess.exe", "FiveM.exe", "FiveM_GTAProcess.exe"]:
                windows.append({
                    'hwnd': hwnd,
                    'title': title,
                    'pid': pid,
                    'process': process.name()
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        return True
    
    win32gui.EnumWindows(enum_callback, windows)
    return windows

def find_gta_windows():
    """Find GTA V windows (when running in FiveM)."""
    windows = []
    
    def enum_callback(hwnd, windows):
        try:
            title = win32gui.GetWindowText(hwnd)
            if title and ("gta" in title.lower() or "grand theft" in title.lower()):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                windows.append({
                    'hwnd': hwnd,
                    'title': title,
                    'pid': pid
                })
        except:
            pass
        return True
    
    win32gui.EnumWindows(enum_callback, windows)
    return windows

def get_window_resolution(hwnd):
    """Get the window resolution (width, height)."""
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        return width, height
    return None

def get_window_position(hwnd):
    """Get the window position (left, top)."""
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        return rect[0], rect[1]
    return None

def get_fivem_resolution():
    """Get FiveM/GTA window resolution and position."""
    print("Searching for FiveM windows...")
    
    # Try to find FiveM windows first
    fivem_windows = find_fivem_windows()
    
    if fivem_windows:
        for win in fivem_windows:
            pass
        
        # Use the first valid window
        win = fivem_windows[0]
        hwnd = win['hwnd']
        resolution = get_window_resolution(hwnd)
        position = get_window_position(hwnd)
        return {
            'found': True,
            'hwnd': hwnd,
            'title': win['title'],
            'pid': win['pid'],
            'process': win['process'],
            'resolution': resolution,
            'position': position,
            'width': resolution[0] if resolution else None,
            'height': resolution[1] if resolution else None,
            'x': position[0] if position else None,
            'y': position[1] if position else None
        }
    
    # If no FiveM windows found, try GTA windows
    print("No FiveM windows found. Searching for GTA windows...")
    gta_windows = find_gta_windows()
    
    if gta_windows:
        for win in gta_windows:
            print(f"  Found: '{win['title']}' (PID: {win['pid']})")
        
        win = gta_windows[0]
        hwnd = win['hwnd']
        resolution = get_window_resolution(hwnd)
        position = get_window_position(hwnd)
        return {
            'found': True,
            'hwnd': hwnd,
            'title': win['title'],
            'pid': win['pid'],
            'process': 'GTA V (FiveM)',
            'resolution': resolution,
            'position': position,
            'width': resolution[0] if resolution else None,
            'height': resolution[1] if resolution else None,
            'x': position[0] if position else None,
            'y': position[1] if position else None
        }
    
    return {'found': False}

def capture_window(hwnd):
    """
    Capture a specific window and return it as an image array.
    
    Args:
        hwnd: Window handle
    
    Returns:
        numpy array of the window image, or None if failed
    """
    if not hwnd:
        return None
    
    try:
        # Get window dimensions
        rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        
        if width <= 0 or height <= 0:
            return None
        
        # Create DC for the window
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        # Create bitmap
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        
        # Print window to DC
        result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
        
        if result != 1:
            # Try alternative method
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
        
        # Convert to numpy array
        bmp_info = bitmap.GetInfo()
        bmp_str = bitmap.GetBitmapBits(True)
        import numpy as np
        img = np.frombuffer(bmp_str, dtype=np.uint8)
        img = img.reshape((height, width, 4))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Cleanup
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        
        return img
        
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None
