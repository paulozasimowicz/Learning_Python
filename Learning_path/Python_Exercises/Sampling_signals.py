# Sampling Signals
# Didn't achieve the goal that I wanted to achieve.

import numpy as np
import matplotlib.pyplot as plt

# Original signal
f = 50  # Hz
t = np.linspace(0, 0.1, 1000)  # 100 ms
x = np.sin(2 * np.pi * f * t)

# Sample intervals in seconds
sample_intervals = [0.005, 0.01, 0.02]
labels = ['5 ms', '10 ms', '20 ms']

plt.figure(figsize=(12, 8))

for i, Ts in enumerate(sample_intervals):
    ts = np.arange(0, 0.1, Ts)
    xs = np.sin(2 * np.pi * f * ts)

    plt.subplot(3, 1, i+1)
    plt.plot(t, x, 'lightgray', label='Original Signal')
    plt.stem(ts, xs, basefmt=" ", label=f'Sampled every {int(Ts*1000)} ms')
    plt.legend()
    plt.grid(True)
    plt.title(f'Sampling Interval = {int(Ts*1000)} ms')

plt.tight_layout()
plt.show()
