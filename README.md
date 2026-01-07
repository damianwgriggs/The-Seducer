
# 🎷 The Seducer
> "Python is a love language."

**The Seducer** is an accessible, AI-driven digital band that writes, improvises, and produces soulful R&B tracks without a single GUI interaction. 

It was built because modern DAWs (Logic, GarageBand) are visual minefields for those with visual disabilities. This project replaces knobs and sliders with pure code, quantum chaos, and algorithmic soul.

---

## 🌹 The Vibe
Most AI music is cold. The Seducer is designed to be intimate.
* **It breathes.** The saxophone improviser has built-in "lung capacity" logic—it pauses to let the track simmer.
* **It listens.** The vocal processor automatically detects your voice and applies a "Barry White" DSP chain.
* **It feels.** The video engine uses physics, not keyframes, to paint a reactive masterpiece.

## 📂 The Architecture of Seduction
The project is split into three distinct modules, each representing a band member:

### 1. The Band (`app.py`)
The Session Leader.
* **Brain:** Uses **Google Gemini** to generate music theory (Scales, Chords, BPM) based on a "Vibe."
* **Heart:** Connects to the **ANU Quantum Random Number Generator** to seed the improvisation with real-time universe chaos.
* **Hands:** Uses **NumPy** to synthesize raw audio waves (Saxophone, Keys, Drums) with analog drift and imperfection.

### 2. The Producer (`mic.py`)
The Engineer.
* **Ears:** Listens to the generated backing track and records your vocals in sync.
* **Touch:** Applies a custom DSP chain:
    * *High-Pass/Low-Pass Filters* to clean static.
    * *Sub-Bass Injection* (filters <250Hz and mixes it back in at 160% volume).
    * *Soft Limiting* (`math.tanh`) for warm analog saturation.

### 3. The Artist (`video.py`)
The Visuals.
* **Eyes:** Analyzes the audio using **Librosa** for RMS (Volume) and Spectral Centroid (Pitch).
* **Brush:** A **PyGame** physics engine where a glowing brush "wanders" the screen, jittering with high notes and swelling with bass.

---

## 🛠️ Installation

1. **Clone the Repo**
   ```bash
   git clone [https://github.com/damianwgriggs/The-Seducer.git](https://github.com/damianwgriggs/The-Seducer.git)
   cd The-Seducer
