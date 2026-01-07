import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
import os
import glob
import time

# --- CONFIGURATION ---
MUSIC_VOLUME = 0.2      # Background music (Very Quiet)
VOCAL_VOLUME = 2.0      # Main Voice (LOUD and CLEAR)
SAMPLE_RATE = 44100     

def find_latest_backing_track():
    files = glob.glob("Soul_Improv_*.wav")
    if not files:
        files = glob.glob("Deep_*.wav") 
    if not files:
        print("ERROR: No backing track found! Run the generator script first.")
        return None
    return max(files, key=os.path.getctime)

def process_vocals_deep(audio, rate):
    """
    1. Removes static/hiss.
    2. Boosts the BASS frequencies to make voice sound deep.
    """
    print("Processing vocals: Removing static + Boosting Bass...")
    
    # --- STEP 1: CLEANING (The Bandpass) ---
    # We keep 60Hz (Deep lows) to 7000Hz (Clarity)
    # Removing frequencies above 7000Hz kills the "static hiss"
    nyquist = 0.5 * rate
    b, a = signal.butter(4, [60.0/nyquist, 7000.0/nyquist], btype='band')
    clean_audio = signal.filtfilt(b, a, audio)
    
    # --- STEP 2: BASS INJECTION (The "Deep" Effect) ---
    # We create a copy of the audio that contains ONLY the bass (under 250Hz)
    b_bass, a_bass = signal.butter(4, 250.0/nyquist, btype='low')
    bass_only = signal.filtfilt(b_bass, a_bass, clean_audio)
    
    # We mix the bass back in, amplified by 50%
    # This artificially thickens the voice
    thick_vocals = clean_audio + (bass_only * 0.6)
    
    return thick_vocals

def record_over_track(backing_filename):
    print(f"\nLOADING TRACK: {backing_filename}")
    file_rate, backing_data = wavfile.read(backing_filename)

    if backing_data.dtype == np.int16:
        backing_data = backing_data.astype(np.float32) / 32768.0

    print(f"DURATION: {len(backing_data)/file_rate:.1f} seconds")
    print("\nIMPORTANT: WEAR HEADPHONES (to prevent echo)!")
    print("GET CLOSER TO THE MIC FOR MORE BASS!")
    print("\nGet ready... Recording starts in 3 seconds.")
    time.sleep(1); print("3...")
    time.sleep(1); print("2...")
    time.sleep(1); print("1... SING!")

    # --- RECORD ---
    recording = sd.playrec(backing_data, samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    print("Recording finished! Mixing...")

    vocals = recording.flatten()
    
    # --- MAGIC PROCESSING ---
    # 1. Apply the Deep Voice Cleaners
    vocals = process_vocals_deep(vocals, SAMPLE_RATE)

    # 2. Match Lengths
    min_len = min(len(backing_data), len(vocals))
    backing_data = backing_data[:min_len]
    vocals = vocals[:min_len]

    # 3. Apply Volume Levels
    backing_quiet = backing_data * MUSIC_VOLUME
    vocals_loud = vocals * VOCAL_VOLUME 

    # 4. Combine
    if backing_quiet.ndim == 1:
        final_mix = backing_quiet + vocals_loud
    else:
        vocals_stereo = vocals_loud[:, np.newaxis]
        final_mix = backing_quiet + vocals_stereo

    # 5. Safety Limiter (Warm Saturation)
    # This is critical because we boosted the bass and volume.
    # It squeezes the sound so it doesn't crackle.
    peak = np.max(np.abs(final_mix))
    if peak > 0.95:
        print("Applying warm compression (limiting peaks)...")
        final_mix = np.tanh(final_mix)

    output_filename = "Final_Deep_Mix.wav"
    wavfile.write(output_filename, SAMPLE_RATE, (final_mix * 32767).astype(np.int16))
    print(f"\nSUCCESS! Saved as: {output_filename}")

if __name__ == "__main__":
    track = find_latest_backing_track()
    if track:
        record_over_track(track)
