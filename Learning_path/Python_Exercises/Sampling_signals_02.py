# Sampling Signals
# Didn't achieve the goal that I wanted to achieve. But got it near it.

import numpy as np
import matplotlib.pyplot as plt

# Generate the base waveform: periodic half-sine wave
t = np.linspace(0, 2, 1000)  # 2 seconds duration
frequency = 1  # 1 Hz
wave = np.abs(np.sin(np.pi * frequency * t))  # Half-sine repeated every second

# Sample the waveform
t_sampled = np.linspace(0, 2, 40)
sampled = np.abs(np.sin(np.pi * frequency * t_sampled))

# Quantization function
def quantize(signal, bits):
    levels = 2 ** bits
    min_val, max_val = 0, 1
    q_levels = np.linspace(min_val, max_val, levels)
    indices = np.digitize(signal, q_levels) - 1
    indices = np.clip(indices, 0, levels - 1)
    return q_levels[indices]

# Plotting
fig, axs = plt.subplots(3, 1, figsize=(10, 8))
bits_list = [1, 2, 3]

for i, bits in enumerate(bits_list):
    q_samples = quantize(sampled, bits)
    axs[i].plot(t, wave, label="Analog Custom Signal", color='orange')
    axs[i].stem(t_sampled, q_samples, basefmt=" ",
                label=f"{bits}-bit Quantized", linefmt='C0-', markerfmt='C0o')
    axs[i].set_title(f"{bits}-bit Sampling Resolution (Smooth Peaked Signal)")
    axs[i].grid(True)
    axs[i].legend()

plt.tight_layout()
plt.show()
