import pygame
import librosa
import numpy as np
import cv2
import sys
import random
import tkinter as tk
from tkinter import filedialog
import math

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1280, 720
FPS = 30

class ArtGen:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Abstract Audio Painter")
        self.clock = pygame.time.Clock()
        
        # Physics
        self.brush_x = WIDTH // 2
        self.brush_y = HEIGHT // 2
        self.angle = 0
        self.velocity = 0
        
        # Video Saver
        self.video_writer = None

    def select_file(self):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
        if not file_path: sys.exit()
        return file_path

    def analyze_audio(self, file_path):
        print("Listening to the song to determine its 'Color Palette'...")
        y, sr = librosa.load(file_path, sr=22050)
        
        # 1. Volume
        hop = 512
        rms = librosa.feature.rms(y=y, hop_length=hop)[0]
        
        # 2. Pitch (Brightness)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
        
        # Normalize (0.0 to 1.0)
        rms = (rms - np.min(rms)) / (np.max(rms) - np.min(rms))
        centroid = (centroid - np.min(centroid)) / (np.max(centroid) - np.min(centroid))
        
        # 3. Determine Song "Signature" (Average Pitch)
        avg_pitch = np.mean(centroid)
        print(f"Song Signature Detected: {avg_pitch:.2f}")
        
        return y, sr, rms, centroid, librosa.get_duration(y=y, sr=sr), avg_pitch

    def draw_gradient_blob(self, surface, x, y, radius, color):
        """
        Draws a soft, glowing circle instead of a flat one.
        We draw 3 layers:
        1. Outer: Large, very transparent (The Glow)
        2. Middle: Medium, semi-transparent
        3. Inner: Small, opaque (The Core)
        """
        # Layer 1: The Glow
        glow_radius = int(radius * 1.5)
        glow_color = (color.r, color.g, color.b, 20) # Very faint
        pygame.draw.circle(surface, glow_color, (x, y), glow_radius)

        # Layer 2: The Body
        body_radius = int(radius)
        body_color = (color.r, color.g, color.b, 50) 
        pygame.draw.circle(surface, body_color, (x, y), body_radius)

        # Layer 3: The Core (Bright center)
        core_radius = int(radius * 0.4)
        core_color = (min(color.r + 50, 255), min(color.g + 50, 255), min(color.b + 50, 255), 100)
        pygame.draw.circle(surface, core_color, (x, y), core_radius)

    def run(self):
        file_path = self.select_file()
        y, sr, rms, pitch_data, duration, avg_pitch = self.analyze_audio(file_path)
        
        # --- SETUP VIDEO ---
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_file = "Abstract_Masterpiece.mp4"
        self.video_writer = cv2.VideoWriter(output_file, fourcc, FPS, (WIDTH, HEIGHT))
        
        # --- SETUP BACKGROUND THEME ---
        # If song is deep (avg_pitch < 0.3): Dark Purple background
        # If song is bright (avg_pitch > 0.6): Dark Teal background
        bg_hue = int(avg_pitch * 240) # Map to Blue/Purple range
        bg_color = pygame.Color(0)
        bg_color.hsva = (bg_hue, 60, 10, 100) # Dark, saturated background
        self.screen.fill(bg_color)

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        start_time = pygame.time.get_ticks()

        running = True
        total_frames = len(rms)
        
        print(f"Painting... (Press Ctrl+C in terminal to stop early)")

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False

            # Time Sync
            curr_time = (pygame.time.get_ticks() - start_time) / 1000.0
            idx = int((curr_time / duration) * total_frames)
            
            if idx >= total_frames:
                running = False
                break

            # --- DATA FOR THIS FRAME ---
            vol = rms[idx]         # 0.0 (Quiet) to 1.0 (Loud)
            pitch = pitch_data[idx] # 0.0 (Deep) to 1.0 (High)

            # --- BRUSH PHYSICS ---
            # 1. Size: Louder = Bigger
            target_radius = 5 + (vol * 120)
            
            # 2. Color: Complex Mixing
            # Base hue comes from the pitch.
            # We add a "twist" so the color evolves over time.
            base_hue = (pitch * 360) 
            # If it's loud, push saturation down (Whiter/Brighter)
            # If it's quiet, high saturation (Deep colors)
            saturation = 100 - (vol * 50) 
            brightness = 50 + (vol * 50)
            
            color = pygame.Color(0)
            color.hsva = (base_hue, saturation, brightness, 100)

            # 3. Movement
            # Pitch affects "nervousness". High pitch = jittery brush.
            jitter = (pitch * 10) 
            
            # Volume affects "swerves". Loud = sharp turns.
            turn_speed = 0.1 + (vol * 0.5)
            self.angle += random.uniform(-turn_speed, turn_speed)
            
            # Speed is pure volume
            step = 2 + (vol * 30)

            self.brush_x += math.cos(self.angle) * step + random.uniform(-jitter, jitter)
            self.brush_y += math.sin(self.angle) * step + random.uniform(-jitter, jitter)

            # Wall Bounce (Instead of teleporting, let's bounce for smoother lines)
            if self.brush_x < 0 or self.brush_x > WIDTH:
                self.angle = math.pi - self.angle # Reflect X
                self.brush_x = max(0, min(WIDTH, self.brush_x))
            if self.brush_y < 0 or self.brush_y > HEIGHT:
                self.angle = -self.angle # Reflect Y
                self.brush_y = max(0, min(HEIGHT, self.brush_y))

            # --- DRAWING ---
            # We draw to a transparent surface first to handle alpha blending correctly
            temp_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            
            # Use our gradient function
            draw_x = int(self.brush_x)
            draw_y = int(self.brush_y)
            self.draw_gradient_blob(temp_surf, draw_x, draw_y, target_radius, color)
            
            # Blit the temp surface onto the main screen
            self.screen.blit(temp_surf, (0, 0))

            pygame.display.flip()

            # --- SAVE VIDEO FRAME ---
            view = pygame.surfarray.array3d(self.screen)
            view = view.transpose([1, 0, 2])
            view = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)
            self.video_writer.write(view)

            self.clock.tick(FPS)

        self.video_writer.release()
        pygame.quit()
        print(f"Masterpiece saved: {output_file}")

if __name__ == "__main__":
    app = ArtGen()
    app.run()
