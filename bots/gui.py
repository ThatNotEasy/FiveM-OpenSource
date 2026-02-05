import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import threading
import time
import pyautogui
import keyboard
from datetime import datetime

sys.path.insert(0, '.')
from modules.windows import get_fivem_resolution
from modules.detect_fish import load_template, detect_template

class FishDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FiveM Fish & Box Detector - Smart Auto Fishing")
        self.root.geometry("1500x1000")
        self.root.minsize(1200, 800)
        
        self.game_region = None
        self.game_resolution = (1280, 720)
        self.threshold = 0.6
        self.is_monitoring = False
        self.monitor_thread = None
        self.game_result = None
        self.fish_count = 0
        self.box_count = 0
        self.caught_count = 0
        self.template_images = {}
        self.current_frame = None
        
        self.keyboard_log = []
        self.spacebar_pressed = False
        self.spacebar_last_press_time = 0
        self.auto_fishing = False
        self.auto_fishing_thread = None
        
        # Fish tracking
        self.fish_y = None
        self.fish_history = []
        self.fish_velocity = 0
        self.predicted_fish_y = None
        
        # Box tracking
        self.box_y = None
        self.box_moving_up = False
        self.box_moving_down = True
        
        self.templates = {
            "fish": "templates/fish.png",
            "box": "templates/box.png"
        }
        
        self.threshold_var = tk.DoubleVar(value=self.threshold)
        
        self.setup_ui()
        self.load_all_templates()
        self.start_keyboard_listener()
        self.start_auto_fishing()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="FiveM Fish & Box Detector - Smart Auto Fishing", 
                  font=("Arial", 18, "bold")).pack(pady=5)
        
        template_frame = ttk.LabelFrame(main_frame, text="Templates", padding="10")
        template_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(template_frame, text="Fish:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.fish_entry = ttk.Entry(template_frame, width=40)
        self.fish_entry.insert(0, self.templates["fish"])
        self.fish_entry.grid(row=0, column=1, padx=5)
        ttk.Button(template_frame, text="Browse", command=lambda: self.browse_template("fish")).grid(row=0, column=2, padx=5)
        self.fish_canvas = tk.Canvas(template_frame, width=80, height=40, bg="gray30")
        self.fish_canvas.grid(row=0, column=3, padx=10)
        
        ttk.Label(template_frame, text="Box:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.box_entry = ttk.Entry(template_frame, width=40)
        self.box_entry.insert(0, self.templates["box"])
        self.box_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(template_frame, text="Browse", command=lambda: self.browse_template("box")).grid(row=1, column=2, padx=5, pady=5)
        self.box_canvas = tk.Canvas(template_frame, width=80, height=40, bg="gray30")
        self.box_canvas.grid(row=1, column=3, padx=10, pady=5)
        
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        auto_frame = ttk.LabelFrame(controls_frame, text="Smart Auto Fishing Settings", padding="10")
        auto_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.auto_fish_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(auto_frame, text="Enable Smart Auto Fishing", 
                       variable=self.auto_fish_var,
                       command=self.toggle_auto_fishing).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(auto_frame, text="Tolerance (px):").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.tolerance_var = tk.IntVar(value=10)
        ttk.Combobox(auto_frame, textvariable=self.tolerance_var,
                                     values=[5, 10, 15, 20, 25], width=5, state="readonly").grid(row=1, column=1, padx=5)
        
        ttk.Label(auto_frame, text="Prediction:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.prediction_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(auto_frame, text="Predict fish movement", 
                       variable=self.prediction_var).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(auto_frame, text="Threshold:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.threshold_slider = ttk.Scale(auto_frame, from_=0.1, to=1.0, 
                                          variable=self.threshold_var, command=self.update_threshold)
        self.threshold_slider.grid(row=3, column=1, padx=5)
        self.threshold_label = ttk.Label(auto_frame, text=f"{self.threshold:.2f}")
        self.threshold_label.grid(row=3, column=2, padx=5)
        
        button_frame = ttk.LabelFrame(controls_frame, text="Controls", padding="10")
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_style = {"width": 12}
        
        self.detect_btn = ttk.Button(button_frame, text="Detect Game", 
                                     command=self.detect_game_region, **btn_style)
        self.detect_btn.grid(row=0, column=0, padx=5, pady=3)
        
        self.start_btn = ttk.Button(button_frame, text="Start", 
                                     command=self.start_monitoring, **btn_style)
        self.start_btn.grid(row=0, column=1, padx=5, pady=3)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", 
                                    command=self.stop_monitoring, **btn_style, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=0, padx=5, pady=3)
        
        ttk.Button(button_frame, text="Clear", 
                   command=self.clear_history, **btn_style).grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Button(button_frame, text="Save Log", 
                   command=self.save_keyboard_log, **btn_style).grid(row=2, column=0, padx=5, pady=3)
        
        ttk.Button(button_frame, text="Exit", 
                   command=self.root.quit, **btn_style).grid(row=2, column=1, padx=5, pady=3)
        
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.game_info_label = ttk.Label(stats_frame, text="Game: Not detected", 
                                         foreground="red", font=("Arial", 11))
        self.game_info_label.pack(side=tk.LEFT, padx=5)
        
        self.fish_info_label = ttk.Label(stats_frame, text="Fish: 0", 
                                         foreground="gray", font=("Arial", 11))
        self.fish_info_label.pack(side=tk.LEFT, padx=15)
        
        self.box_info_label = ttk.Label(stats_frame, text="Box: 0", 
                                         foreground="gray", font=("Arial", 11))
        self.box_info_label.pack(side=tk.LEFT, padx=15)
        
        self.caught_label = ttk.Label(stats_frame, text="Caught: 0", 
                                      foreground="gray", font=("Arial", 11))
        self.caught_label.pack(side=tk.LEFT, padx=15)
        
        self.fishing_status_label = ttk.Label(stats_frame, text="Status: OFF", 
                                              foreground="gray", font=("Arial", 11, "bold"))
        self.fishing_status_label.pack(side=tk.LEFT, padx=30)
        
        self.pos_info_label = ttk.Label(stats_frame, text="Fish: - | Box: - | Pred: -", 
                                        foreground="gray", font=("Arial", 10))
        self.pos_info_label.pack(side=tk.LEFT, padx=15)
        
        video_frame = ttk.LabelFrame(main_frame, text="Live Video - Green Fish | Blue Box | Yellow Prediction", padding="5")
        video_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(video_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        log_frame = ttk.LabelFrame(main_frame, text="Action Log", padding="5")
        log_frame.pack(fill=tk.X, pady=5)
        
        self.log_text = tk.Text(log_frame, width=100, height=6, bg="black", fg="lime", 
                                 font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Click 'Detect Game' to start")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                               relief=tk.SUNKEN, font=("Arial", 10))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
    
    def browse_template(self, template_type):
        filename = filedialog.askopenfilename(title=f"Select {template_type.capitalize()} Template", 
                                               filetypes=[("PNG", "*.png")])
        if filename:
            if template_type == "fish":
                self.fish_entry.delete(0, tk.END)
                self.fish_entry.insert(0, filename)
                self.templates["fish"] = filename
            else:
                self.box_entry.delete(0, tk.END)
                self.box_entry.insert(0, filename)
                self.templates["box"] = filename
            self.load_template(template_type)
    
    def update_threshold(self, value):
        self.threshold = float(value)
        self.threshold_label.config(text=f"{self.threshold:.2f}")
    
    def load_all_templates(self):
        self.load_template("fish")
        self.load_template("box")
    
    def load_template(self, template_type):
        try:
            path = self.templates[template_type]
            template = load_template(path)
            self.template_images[template_type] = template
            
            canvas = self.fish_canvas if template_type == "fish" else self.box_canvas
            canvas.delete("all")
            
            template_rgb = cv2.cvtColor(template, cv2.COLOR_BGR2RGB)
            template_small = cv2.resize(template_rgb, (80, 40))
            pil_template = Image.fromarray(template_small)
            photo = ImageTk.PhotoImage(pil_template)
            
            canvas.create_image(40, 20, image=photo)
            canvas.image = photo
            
        except Exception as e:
            self.log_action(f"Error loading {template_type}: {e}")
    
    def start_keyboard_listener(self):
        def listen():
            while True:
                try:
                    event = keyboard.read_event()
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    if event.name == "space":
                        if event.event_type == "down" and not self.spacebar_pressed:
                            self.spacebar_pressed = True
                            self.spacebar_last_press_time = time.time()
                            self.log_action(f"[{timestamp}] SPACEBAR PRESSED - Moving UP")
                        elif event.event_type == "up" and self.spacebar_pressed:
                            self.spacebar_pressed = False
                            self.log_action(f"[{timestamp}] SPACEBAR RELEASED - Falling")
                    
                except:
                    time.sleep(0.1)
        
        threading.Thread(target=listen, daemon=True).start()
    
    def start_auto_fishing(self):
        def auto_fish_loop():
            while True:
                try:
                    if self.auto_fishing and self.auto_fish_var.get() and self.is_monitoring:
                        if self.current_frame is not None:
                            self.smart_fishing_control()
                    
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"Auto fishing error: {e}")
                    time.sleep(0.1)
        
    def smart_fishing_control(self):
        """Smart fishing control with prediction and debouncing."""
        tolerance = self.tolerance_var.get()
        
        # Get current positions
        current_fish_y = self.fish_y
        current_box_y = self.box_y
        predicted_y = self.predicted_fish_y
        
        if current_fish_y is None or current_box_y is None:
            return
        
        # Track press duration to prevent chattering
        if not hasattr(self, 'spacebar_press_start_time'):
            self.spacebar_press_start_time = 0
        
        # Minimum hold time to prevent rapid toggling (ms)
        min_hold_time = 300  
        
        # Hysteresis: release threshold is wider than press threshold
        release_tolerance = tolerance * 2.5
        
        # Calculate distance to predicted position
        target_y = predicted_y if predicted_y is not None else current_fish_y
        diff = target_y - current_box_y
        
        # Smart control logic with debouncing
        if abs(diff) > tolerance:
            if diff < 0:
                # Target is ABOVE box - need to move UP
                if not self.spacebar_pressed:
                    # Check if we should press
                    press_time = time.time()
                    time_since_release = (press_time - self.spacebar_press_start_time) * 1000 if self.spacebar_press_start_time > 0 else 1000
                    
                    if time_since_release > 100:  # Debounce: wait 100ms after release
                        self.log_action(f"[AUTO] Press | Fish:{int(current_fish_y)} | Box:{int(current_box_y)} | Tgt:{int(target_y)} | Diff:{int(diff)}")
                        keyboard.press("space")
                        self.spacebar_pressed = True
                        self.spacebar_press_start_time = press_time
                        self.fishing_status_label.config(
                            text=f"Status: MOVING UP (diff: {diff})", foreground="orange"
                        )
            else:
                # Target is BELOW box - need to fall
                if self.spacebar_pressed:
                    # Check minimum hold time before releasing
                    hold_duration = (time.time() - self.spacebar_press_start_time) * 1000
                    
                    if hold_duration >= min_hold_time or current_box_y > target_y + release_tolerance:
                        self.log_action(f"[AUTO] Release | Fish:{int(current_fish_y)} | Box:{int(current_box_y)} | Tgt:{int(target_y)} | Diff:{int(diff)} | Hold:{int(hold_duration)}ms")
                        keyboard.release("space")
                        self.spacebar_pressed = False
                        self.spacebar_press_start_time = time.time()
                        self.fishing_status_label.config(
                            text=f"Status: FALLING (diff: {diff})", foreground="blue"
                        )
        else:
            # Very close - aligned!
            if self.spacebar_pressed:
                hold_duration = (time.time() - self.spacebar_press_start_time) * 1000
                
                # Only release if we've held long enough
                if hold_duration >= min_hold_time:
                    self.log_action(f"[AUTO] ALIGNED! | Fish:{int(current_fish_y)} | Box:{int(current_box_y)} | Pred:{int(predicted_y)} | Hold:{int(hold_duration)}ms")
                    keyboard.release("space")
                    self.spacebar_pressed = False
                    self.spacebar_press_start_time = time.time()
                    self.fishing_status_label.config(
                        text=f"Status: CATCHING at Y={int(target_y)}", foreground="lime"
                    )
                    
                    # Check if caught (box must be close to fish, and we need to be falling)
                    if abs(current_fish_y - current_box_y) < tolerance:
                        self.caught_count += 1
                        self.caught_label.config(text=f"Caught: {self.caught_count}", foreground="green")
                        self.log_action(f"[AUTO] FISH CAUGHT! #{self.caught_count}")
        
        # Update position display
        self.pos_info_label.config(
            text=f"Fish: {int(current_fish_y) if current_fish_y else '-'} | Box: {int(current_box_y)} | Pred: {int(predicted_y) if predicted_y else '-'}",
            foreground="white"
        )
    
    def toggle_auto_fishing(self):
        if self.auto_fish_var.get():
            self.log_action("Smart Auto Fishing ENABLED - Will predict and control spacebar")
            self.fishing_status_label.config(text="Status: READY", foreground="green")
        else:
            self.log_action("Auto Fishing DISABLED")
            self.fishing_status_label.config(text="Status: OFF", foreground="gray")
            if self.spacebar_pressed:
                keyboard.release("space")
                self.spacebar_pressed = False
    
    def log_position(self):
        """Log fish and box positions periodically."""
        if self.is_monitoring and (self.fish_y is not None or self.box_y is not None):
            fish_y = int(self.fish_y) if self.fish_y is not None else "N/A"
            box_y = int(self.box_y) if self.box_y is not None else "N/A"
            pred_y = int(self.predicted_fish_y) if self.predicted_fish_y is not None else "N/A"
            space_state = "HELD" if self.spacebar_pressed else "FREE"
            
            self.log_action(f"[POS] Fish Y: {fish_y} | Box Y: {box_y} | Pred: {pred_y} | Space: {space_state}")
    
    def log_action(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        self.keyboard_log.append(log_entry)
        self.root.after(0, self.update_log_display, log_entry)
        print(log_entry)
    
    def update_log_display(self, entry):
        self.log_text.insert(tk.END, entry + "\n")
        self.log_text.see(tk.END)
        
        if "PRESS" in entry or "UP" in entry:
            self.log_text.tag_add("up", "end-2l", "end-1l")
            self.log_text.tag_config("up", foreground="orange")
        elif "RELEASE" in entry or "FALL" in entry:
            self.log_text.tag_add("down", "end-2l", "end-1l")
            self.log_text.tag_config("down", foreground="cyan")
        elif "ALIGNED" in entry or "CAUGHT" in entry:
            self.log_text.tag_add("auto", "end-2l", "end-1l")
            self.log_text.tag_config("auto", foreground="lime")
    
    def save_keyboard_log(self):
        filename = f"fishing_log_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for entry in self.keyboard_log:
                f.write(entry + "\n")
        self.set_status(f"Log saved to {filename}")
    
    def set_status(self, text):
        self.status_var.set(text)
    
    def clear_history(self):
        self.fish_count = 0
        self.box_count = 0
        self.caught_count = 0
        self.fish_y = None
        self.box_y = None
        self.predicted_fish_y = None
        self.fish_history = []
        self.fish_velocity = 0
        self.fish_info_label.config(text="Fish: 0", foreground="gray")
        self.box_info_label.config(text="Box: 0", foreground="gray")
        self.caught_label.config(text="Caught: 0", foreground="gray")
        self.pos_info_label.config(text="Fish: - | Box: - | Pred: -", foreground="gray")
        self.log_text.delete(1.0, tk.END)
        self.keyboard_log = []
    
    def detect_game_region(self):
        def run():
            self.set_status("Detecting game window...")
            self.detect_btn.config(state=tk.DISABLED)
            self.start_btn.config(state=tk.DISABLED)
            
            try:
                game_result = get_fivem_resolution()
                self.game_result = game_result
                
                if game_result['found']:
                    x, y = game_result['x'], game_result['y']
                    w, h = game_result['width'], game_result['height']
                    self.game_region = (x, y, w, h)
                    self.game_resolution = (w, h)
                    
                    self.game_info_label.config(
                        text=f"Game: {game_result['title'][:30]} | {w}x{h}",
                        foreground="green"
                    )
                    self.set_status("Game detected! Click 'Start'")
                    
                    frame = self.capture_frame()
                    if frame is not None:
                        self.current_frame = frame
                        self.display_video(frame)
                    
                else:
                    self.game_info_label.config(text="Game not found!", foreground="red")
                    self.set_status("Please start FiveM first")
                
                self.detect_btn.config(state=tk.NORMAL)
                self.start_btn.config(state=tk.NORMAL)
                
            except Exception as e:
                self.set_status(f"Error: {str(e)}")
                self.detect_btn.config(state=tk.NORMAL)
                self.start_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=run, daemon=True).start()
    
    def capture_frame(self):
        if self.game_region is None:
            return None
        x, y, w, h = self.game_region
        try:
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except:
            return None
    
    def start_monitoring(self):
        if self.game_region is None:
            self.set_status("Detect game first!")
            return
        
        self.is_monitoring = True
        self.detect_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log_action("Started monitoring - Smart fishing active")
        self.set_status("Monitoring started!")
        
        self.monitor_thread = threading.Thread(target=self.monitor_function, daemon=True)
        self.monitor_thread.start()
        
        self.update_display_loop()
    
    def stop_monitoring(self):
        self.is_monitoring = False
        self.detect_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.spacebar_pressed:
            keyboard.release("space")
            self.spacebar_pressed = False
        
        self.log_action(f"Stopped | Fish: {self.fish_count} | Box: {self.box_count}")
        self.set_status("Stopped")
    
    def monitor_function(self):
        while self.is_monitoring:
            try:
                frame = self.capture_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue
                
                overlay = frame.copy()
                
                for template_type, template in self.template_images.items():
                    if template is None:
                        continue
                    
                    result = detect_template(frame, template, self.threshold)
                    
                    if result['found']:
                        if template_type == "fish":
                            self.fish_count += 1
                            self.fish_y = result['center_y']
                            
                            # Update fish history for prediction with smoothing
                            self.fish_history.append(self.fish_y)
                            if len(self.fish_history) > 10:
                                self.fish_history.pop(0)
                            
                            # Apply median filter to reduce noise (use median of last 3 positions)
                            if len(self.fish_history) >= 3:
                                sorted_y = sorted(self.fish_history[-3:])
                                smoothed_fish_y = sorted_y[1]  # Median
                            else:
                                smoothed_fish_y = self.fish_y
                            
                            # Calculate velocity using smoothed positions
                            if len(self.fish_history) >= 2:
                                raw_velocity = self.fish_history[-1] - self.fish_history[-2]
                                # Clamp velocity to reasonable range
                                max_velocity = 50
                                self.fish_velocity = max(-max_velocity, min(max_velocity, raw_velocity))
                            
                            # Predict next position using smoothed velocity
                            if self.prediction_var.get() and len(self.fish_history) >= 2:
                                self.predicted_fish_y = smoothed_fish_y + self.fish_velocity * 2
                            else:
                                self.predicted_fish_y = smoothed_fish_y
                            
                            self.fish_info_label.config(
                                text=f"Fish #{self.fish_count} ({result['confidence']:.1%})", 
                                foreground="green"
                            )
                            color = (0, 255, 0)
                        else:
                            self.box_count += 1
                            self.box_y = result['center_y']
                            self.box_info_label.config(
                                text=f"Box #{self.box_count} ({result['confidence']:.1%})", 
                                foreground="blue"
                            )
                            color = (255, 0, 0)
                        
                        x, y, w, h = result['x'], result['y'], result['width'], result['height']
                        cx, cy = result['center_x'], result['center_y']
                        
                        cv2.rectangle(overlay, (x, y), (x+w, y+h), color, 3)
                        cv2.circle(overlay, (cx, cy), 5, color, 2)
                        cv2.putText(overlay, f"{template_type.upper()} #{self.fish_count if template_type=='fish' else self.box_count}", 
                                    (x, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        cv2.putText(overlay, f"Y={int(cy)}", (x, y+h+15), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        
                        # Draw prediction point for fish
                        if template_type == "fish" and self.predicted_fish_y is not None:
                            pred_y = int(self.predicted_fish_y)
                            cv2.circle(overlay, (cx, pred_y), 8, (0, 255, 255), 2)
                            cv2.putText(overlay, f"Pred Y={pred_y}", (x + w + 5, pred_y), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                        
                        # Draw line between fish and box
                        if self.fish_y is not None and self.box_y is not None and template_type == "fish":
                            bx = result['center_x']
                            cv2.line(overlay, (bx, int(self.fish_y)), (bx, int(self.box_y)), (0, 255, 255), 1)
                
                # Log positions periodically
                self.log_position()
                
                self.current_frame = overlay.copy()
                time.sleep(0.05)
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(0.1)
    
    def update_display_loop(self):
        if self.is_monitoring and self.current_frame is not None:
            self.display_video(self.current_frame)
            self.root.after(30, self.update_display_loop)
    
    def display_video(self, cv2_image):
        try:
            rgb = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
            
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            
            if cw < 100 or ch < 100:
                return
            
            game_w, game_h = self.game_resolution
            if game_w > 0 and game_h > 0:
                ratio = min(cw / game_w, ch / game_h)
                new_w = int(game_w * ratio)
                new_h = int(game_h * ratio)
            else:
                ratio = min(cw / rgb.shape[1], ch / rgb.shape[0])
                new_w = int(rgb.shape[1] * ratio)
                new_h = int(rgb.shape[0] * ratio)
            
            resized = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            pil = Image.fromarray(resized)
            photo = ImageTk.PhotoImage(pil)
            
            self.canvas.delete("all")
            x_off = (cw - new_w) // 2
            y_off = (ch - new_h) // 2
            self.canvas.create_image(x_off, y_off, anchor=tk.NW, image=photo)
            self.canvas.image = photo
            
        except Exception as e:
            pass


def main():
    root = tk.Tk()
    app = FishDetectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
