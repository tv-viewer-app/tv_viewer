"""App icon generation and embedded icon data."""

import base64
import io
import os

# Embedded ICO file as base64 (32x32 TV icon)
ICON_BASE64 = """
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
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZGQAN
GRk4WhkZV4UZGVeFGRk4WRkZAAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
GRkJCBkZXpQZGbD0GRnE/xkZxP8ZGbD0GRlekxkZCQcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAZGRgfGRmDxxkZxv8ZGcn/GRnJ/xkZxv8ZGYPGGRkYHgAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAGRkkLhkZlNwZGcn/GRnJ/xkZyf8ZGcn/GRmU2xkZJC0AAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABkZIC8ZGY/WGRnH/xkZyf8ZGcf/GRmP1RkZIC4A
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZGRIYGRlvsBkZvf8ZGb3/GRlv
rhkZEhcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABkZBAQZGTlX
GRlVfhkZVX4ZGTlWGRkEAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//w////4H///8A///8AH//+AB//+AAf/+AAH
/9gAA/+AAAP/AAAD/gAAAf4AAAD+AAAA/gAAAP4AAAD8AAAAfAAAAPwAAAH+AAAB/wAAAf+AAAH/
4AAD/+AAA//4AAf/+AAf//wAf///gf///8f///////ggP//wAA//4AAH/+AAB//wAAf/+AAf//8/
/w==
"""

def get_icon_path() -> str:
    """Get path to icon file, creating it if needed."""
    icon_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(icon_dir, "tv_viewer.ico")
    
    if not os.path.exists(icon_path):
        try:
            # Decode and save the icon
            icon_data = base64.b64decode(ICON_BASE64.strip())
            with open(icon_path, 'wb') as f:
                f.write(icon_data)
        except Exception as e:
            print(f"Could not create icon file: {e}")
            return ""
    
    return icon_path


def set_window_icon(window):
    """Set the window icon for a tkinter window."""
    try:
        icon_path = get_icon_path()
        if not icon_path or not os.path.exists(icon_path):
            print(f"Icon file not found at {icon_path}")
            return
        
        print(f"Setting icon from: {icon_path}")
        
        # On Windows, iconbitmap works with .ico files
        # Linux requires different syntax
        import platform
        try:
            if platform.system() == 'Windows':
                window.iconbitmap(default=icon_path)
            else:
                window.iconbitmap(icon_path)
            print("Icon set successfully with iconbitmap")
            return
        except Exception as e:
            print(f"iconbitmap failed: {e}")
        
        # Fallback: try using PhotoImage for iconphoto
        try:
            import tkinter as tk
            # Try with PIL if available
            from PIL import Image, ImageTk
            img = Image.open(icon_path)
            # Convert to multiple sizes for better display
            img_resized = img.resize((32, 32), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_resized)
            window.iconphoto(True, photo)
            window._icon_photo = photo  # Keep reference
            print("Icon set successfully with iconphoto (PIL)")
        except ImportError:
            # No PIL, try native PhotoImage (limited format support)
            try:
                photo = tk.PhotoImage(file=icon_path)
                window.iconphoto(True, photo)
                window._icon_photo = photo
                print("Icon set successfully with iconphoto (native)")
            except Exception as e2:
                print(f"Native PhotoImage failed: {e2}")
        except Exception as e:
            print(f"PIL iconphoto failed: {e}")
    except Exception as e:
        print(f"Could not set window icon: {e}")


# Alternative: Generate icon programmatically using PIL
def create_icon_with_pil():
    """Create icon using PIL (requires Pillow)."""
    try:
        from PIL import Image, ImageDraw
        
        # Create 32x32 image with transparency
        size = 32
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw TV body (blue rectangle with rounded corners)
        tv_color = (25, 25, 112)  # Midnight blue
        screen_color = (30, 144, 255)  # Dodger blue
        
        # TV outer body
        draw.rounded_rectangle([4, 6, 28, 24], radius=2, fill=tv_color)
        
        # Screen (inner rectangle)
        draw.rectangle([6, 8, 26, 22], fill=screen_color)
        
        # TV stand
        draw.rectangle([12, 24, 20, 26], fill=tv_color)
        draw.rectangle([10, 26, 22, 28], fill=tv_color)
        
        # Antenna
        draw.line([10, 6, 6, 2], fill=tv_color, width=2)
        draw.line([22, 6, 26, 2], fill=tv_color, width=2)
        
        # Save as ICO
        icon_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(icon_dir, "tv_viewer.ico")
        img.save(icon_path, format='ICO', sizes=[(32, 32)])
        
        return icon_path
    except ImportError:
        return None
    except Exception as e:
        print(f"Could not create icon with PIL: {e}")
        return None
