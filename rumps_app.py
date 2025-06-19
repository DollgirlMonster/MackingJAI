import rumps
import threading
import signal
import os
import sys
import subprocess
from server import run_server

# # util function 
# def check_shortcut():
#     shortcuts = subprocess.run(["Shortcuts", "list"], capture_output=True, text=True)
#     shortcuts = shortcuts.stdout.splitlines()
#     if "MackingJAI" in shortcuts:
#         return True
#     return False

class FlaskServerApp(rumps.App):
    def __init__(self):
        # Use the icon file instead of emoji
        super(FlaskServerApp, self).__init__("MackingJAI", icon="iconbw.icns", quit_button=None)
        
        # Create menu items with key equivalents
        status_item = rumps.MenuItem("MackingJAI is Running")
        
        # Add shortcut installation menu item
        install_shortcut_item = rumps.MenuItem("Install Shortcut")
        
        # For Cmd+Q, we need to specify it during creation
        quit_item = rumps.MenuItem("Quit", key="q")
        
        # Set menu with created items
        self.menu = [status_item, None, install_shortcut_item, None, quit_item]
        
        # Set callbacks for menu items
        quit_item.set_callback(self.quit_app)
        install_shortcut_item.set_callback(self.install_shortcut)
        
        self.flask_thread = None
        self.start_server()
    
    def install_shortcut(self, _):
        # Replace with your actual iCloud shortcut link
        shortcut_url = "https://www.icloud.com/shortcuts/508acd78c215490394c4a70c902dbb58"
        subprocess.run(['open', shortcut_url])
        
    def start_server(self):
        # Start Flask server in a separate thread
        self.flask_thread = threading.Thread(target=run_server)
        self.flask_thread.daemon = True
        self.flask_thread.start()
    
    def quit_app(self, _):
        # Clean shutdown of the Flask server
        os._exit(0)  # This ensures everything is terminated

def main():
    # Setup signal handlers for clean termination
    def signal_handler(sig, frame):
        os._exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the rumps app
    FlaskServerApp().run()

if __name__ == '__main__':
    main()