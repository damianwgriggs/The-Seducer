import numpy as np
import scipy.io.wavfile as wavfile
import requests
import secrets
import hashlib
import time
import json
import google.generativeai as genai
import random

# --- CONFIGURATION ---
# !!! PASTE YOUR API KEY HERE !!!
GOOGLE_API_KEY = "YOURAPIKEYPASTEHERE"

MODEL_NAME = 'gemini-2.5-flash'
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

SAMPLE_RATE = 44100
TARGET_DURATION_SECONDS = 130 

# --- 1. CHAOS ENGINE (The Soul Source) ---
def get_quantum_seed():
    hw = secrets.token_bytes(32)
    qw = b''
    try:
        # Fetch real quantum randomness from ANU
        url = "https://qrng.anu.edu.au/API/jsonI.php?length=1&type=hex16&size=32"
        r = requests.get(url, timeout=1)
        if r.status_code == 200:
            qw = bytes.fromhex(r.json()['data'][0])
    except:
        pass
    tw = str(time.time_ns()).encode()
    hasher = hashlib.sha256()
    hasher.update(hw + qw + tw)
    seed = int(hasher.hexdigest(), 16) % (2**32)
    
    # SEED PYTHON'S RANDOMNESS WITH THIS HARDWARE SEED
    # This ensures the "Improv" is unique to this specific moment/hardware state.
    random.seed(seed)
    np.random.seed(seed % (2**32))
    
    print(f"--- QUANTUM SOUL SEED: {seed} ---")
    return seed

# --- 2. THE SESSION LEADER (AI) ---
# We only ask the AI for the "Sheet Music" (Chords/Scale), NOT the notes.
def get_session_params(seed):
    print(f"Contacting {MODEL_NAME} for Session Sheet Music...")
    
    prompt = f"""
    You are a Jazz Bandleader. Seed: {seed}.
    Define a 2-chord "Vamp" for a soulful R&B track (Style: Sade, Grover Washington).
    
    JSON Structure:
    {{
      "bpm": integer (75-85),
      "root_freq": float (Low F/F# ~43.0),
      "scale_intervals": [0, 3, 5, 7, 10], // Minor Pentatonic or Dorian
      "chord_1": [float_freqs], // e.g. Fm9
      "chord_2": [float_freqs]  // e.g. Bb13
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        start_idx = text.find('{')
        end_idx = text.rfind('}') + 1
        return json.loads(text[start_idx:end_idx])
    except:
        return None

# --- 3. THE IMPROVISER (Python Logic) ---
# This replaces the AI generation for notes. It "plays" live.

def get_scale_notes(root, intervals, octave_range=2):
    """Generates a pool of valid notes for the Sax to choose from."""
    pool = []
    base_freqs = [root * (2**(i/12)) for i in intervals]
    for octave in range(1, octave_range + 2):
        for f in base_freqs:
            pool.append(f * (2**octave))
    return sorted(pool)

class SoulImproviser:
    def __init__(self, scale_notes):
        self.scale = scale_notes
        self.last_note_idx = len(scale_notes) // 2 # Start in middle
        
    def play_lick(self, intensity=0.5):
        """Generates a jazz phrase (lick) based on current intensity."""
        phrase = []
        
        # Soul Rule 1: Breathe. Don't play all the time.
        if random.random() > intensity: 
            return [] # Rest for this bar
            
        # Determine phrase length
        num_notes = random.randint(3, 8) if intensity > 0.6 else random.randint(1, 4)
        
        current_step = 0
        for _ in range(num_notes):
            # Walk up/down the scale (stepwise motion is more melodic than random jumps)
            step_jump = random.choice([-1, -1, 0, 1, 1, 2, -2])
            self.last_note_idx = max(0, min(len(self.scale)-1, self.last_note_idx + step_jump))
            
            freq = self.scale[self.last_note_idx]
            
            # Rhythm: Syncopation
            # Choose a start step (16th notes): 0, 2, 3, 6, etc.
            duration = random.choice([2, 4, 8]) # Short, Medium, Long
            start_step = current_step + random.choice([2, 4])
            
            phrase.append({"step": start_step, "freq": freq, "dur": duration})
            current_step = start_step + duration
            
        return phrase

# --- 4. DSP INSTRUMENTS (Soulful & Imperfect) ---

def mix(master, sound, loc, vol=1.0):
    if loc < 0: return
    if loc + len(sound) >= len(master):
        avail = len(master) - loc
        if avail <= 0: return
        sound = sound[:avail]
    master[loc:loc+len(sound)] += sound * vol

# -- Drifting Keys (Analog Pitch Drift) --
def synth_keys_drift(freqs, duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    master = np.zeros_like(t)
    
    for f in freqs:
        if f > 800: f /= 2 
        
        # PITCH DRIFT: The "Warble" of old tape
        drift = 1.0 + 0.002 * np.sin(2 * np.pi * 0.5 * t + random.random())
        
        # Smooth FM Tone
        mod = np.sin(2 * np.pi * f * t) * f * 0.5 * np.exp(-5 * t)
        carrier = np.sin(2 * np.pi * (f * drift) * t + mod)
        master += carrier

    env = np.ones_like(t)
    env[:1000] = np.linspace(0, 1, 1000)
    env[-5000:] = np.linspace(1, 0, 5000)
    
    return master * env * 0.3

# -- Expressive Sax (Vibrato changes over time) --
def synth_sax_soul(freq, duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    
    # Expressive Vibrato: Starts flat, then widens (classic soul technique)
    vib_envelope = np.linspace(0, 1, len(t)) ** 2 # Delayed vibrato
    vib = freq * 0.015 * np.sin(2 * np.pi * 5.5 * t) * vib_envelope
    
    # Pitch Bend (Scoop up into the note)
    scoop = np.exp(-20 * t) * -20 # Starts 20Hz flat, quickly corrects
    
    freq_mod = freq + vib + scoop
    phase = 2 * np.pi * np.cumsum(freq_mod) / SAMPLE_RATE
    
    # Waveform: Saturation
    tone = np.tanh(np.sin(phase) * 2.5)
    
    # Breath/Air noise
    breath = np.random.uniform(-0.05, 0.05, len(t))
    
    # Dynamics Envelope
    env = np.ones_like(t)
    attack = int(0.08 * SAMPLE_RATE)
    env[:attack] = np.linspace(0, 1, attack)
    env[-attack:] = np.linspace(1, 0, attack)
    
    return (tone + breath) * env * 0.45

# -- The Groove Section --
def synth_kick_thump():
    t = np.linspace(0, 0.3, int(SAMPLE_RATE * 0.3))
    freq = 70 * np.exp(-10 * t) + 30
    return np.sin(2 * np.pi * freq * t) * np.exp(-6 * t)

def synth_snare_rim():
    t = np.linspace(0, 0.1, int(SAMPLE_RATE * 0.1))
    return (np.random.uniform(-0.6, 0.6, len(t)) + np.sin(2*np.pi*400*t)) * np.exp(-20*t) * 0.6

def synth_hat_soft():
    t = np.linspace(0, 0.05, int(SAMPLE_RATE * 0.05))
    return np.random.uniform(-0.4, 0.4, len(t)) * np.exp(-40*t) * 0.3

# --- MAIN ENGINE ---
def generate_soul_track():
    if GOOGLE_API_KEY == "myapikey":
        print("ERROR: Paste API Key")
        return

    seed = get_quantum_seed()
    
    # 1. Ask AI for the "Vibe" (Scale & Chords)
    params = get_session_params(seed)
    if not params: return

    bpm = params.get("bpm", 80)
    root = params.get("root_freq", 43.65)
    intervals = params.get("scale_intervals", [0, 3, 5, 7, 10])
    chord1 = params.get("chord_1", [root*2, root*2.4])
    chord2 = params.get("chord_2", [root*3, root*3.6])
    
    print(f"BPM: {bpm} | Key: {root:.1f}Hz")

    # 2. Setup Timing
    beat_dur = 60 / bpm
    step_len = beat_dur / 4
    bar_dur = beat_dur * 4
    
    # 3. Setup Improviser
    scale_notes = get_scale_notes(root, intervals)
    sax_player = SoulImproviser(scale_notes)
    
    # 4. Define Structure
    # 4 bars Intro (Solo), 16 bars Verse (Quiet), 8 bars Chorus (Licks), 8 bars Verse, 4 bars Outro (Solo)
    structure = ["Intro"]*4 + ["Verse"]*16 + ["Chorus"]*8 + ["Verse"]*8 + ["Outro"]*4
    
    total_samples = int(len(structure) * bar_dur * SAMPLE_RATE)
    master = np.zeros(total_samples + 88200)
    
    kick = synth_kick_thump()
    snare = synth_snare_rim()
    hat = synth_hat_soft()
    
    print(f"Improvising over {len(structure)} bars...")
    
    for bar_idx, section in enumerate(structure):
        bar_offset_samples = int(bar_idx * bar_dur * SAMPLE_RATE)
        
        # --- A. DRUMS (Humanized) ---
        # Basic Groove: Kick on 1, Snare on 3 (Half time feel)
        # Add random "ghost notes"
        
        # Beat 1 (Kick)
        mix(master, kick, bar_offset_samples) 
        # Beat 2 (Hat)
        mix(master, hat, bar_offset_samples + int(beat_dur * SAMPLE_RATE))
        # Beat 3 (Snare + Kick lag)
        mix(master, snare, bar_offset_samples + int(beat_dur * 2 * SAMPLE_RATE))
        # Beat 4 (Hat)
        mix(master, hat, bar_offset_samples + int(beat_dur * 3 * SAMPLE_RATE))
        
        # Random Fills (Ghost kicks)
        if random.random() > 0.7:
             mix(master, kick, bar_offset_samples + int(beat_dur * 2.5 * SAMPLE_RATE), vol=0.6)

        # --- B. KEYS (Comping) ---
        # Switch chords every bar (Vamp)
        current_chord = chord1 if bar_idx % 2 == 0 else chord2
        
        # Play chord at start of bar
        mix(master, synth_keys_drift(current_chord, bar_dur), bar_offset_samples, vol=0.5)
        
        # --- C. SAXOPHONE (The Soul) ---
        # Determine intensity based on section
        intensity = 0.0
        if section == "Intro" or section == "Outro":
            intensity = 0.9 # Soloing hard
        elif section == "Chorus":
            intensity = 0.4 # Tasty licks
        elif section == "Verse":
            intensity = 0.1 # Very sparse (leave room for vocals)
            
        # Get Lick from Improviser Class
        lick = sax_player.play_lick(intensity)
        
        for note in lick:
            # Humanize Timing: Play slightly "behind the beat" (lag)
            lag = random.randint(1000, 5000) 
            
            t_start = bar_offset_samples + int(note["step"] * step_len * SAMPLE_RATE) + lag
            mix(master, synth_sax_soul(note["freq"], note["dur"] * step_len), t_start)

    # Finalize
    master = master[:total_samples]
    max_val = np.max(np.abs(master))
    if max_val > 0: master = master / max_val * 0.95

    filename = f"Soul_Improv_{seed}.wav"
    wavfile.write(filename, SAMPLE_RATE, (master * 32767).astype(np.int16))
    print(f"DONE. Soul captured in: {filename}")

if __name__ == "__main__":
    generate_soul_track()
