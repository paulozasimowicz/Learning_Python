import control as ctrl
import numpy as np
import matplotlib.pyplot as plt

def get_plant():
    print("Enter the plant transfer function G(s):")
    num = list(map(float, input("Numerator coefficients (e.g. 2): ").split()))
    den = list(map(float, input("Denominator coefficients (e.g. 3 1): ").split()))
    return ctrl.tf(num, den)

def get_pid_controller(method="manual"):
    if method == "manual":
        print("\nManual PID Tuning:")
        Kp = float(input("Enter Kp: "))
        Ki = float(input("Enter Ki: "))
        Kd = float(input("Enter Kd: "))
    elif method == "zn":
        print("\nZiegler-Nichols Tuning:")
        Ku = float(input("Enter Ultimate Gain (Ku): "))
        Pu = float(input("Enter Ultimate Period (Pu): "))
        Kp = 0.6 * Ku
        Ki = 1.2 * Ku / Pu
        Kd = 3 * Ku * Pu / 40
        print(f"Tuned PID Gains -> Kp: {Kp:.3f}, Ki: {Ki:.3f}, Kd: {Kd:.3f}")
    else:
        raise ValueError("Invalid PID method.")

    return ctrl.tf([Kd, Kp, Ki], [1, 0])

def generate_input_signal(input_type, t):
    if input_type == "step":
        return np.ones_like(t)
    elif input_type == "pulse":
        amp = float(input("Enter pulse amplitude: "))
        width = float(input("Enter pulse width (in seconds): "))
        signal = np.zeros_like(t)
        signal[t <= width] = amp
        return signal
    elif input_type == "sine":
        amp = float(input("Enter sine amplitude: "))
        freq = float(input("Enter sine frequency (rad/s): "))
        return amp * np.sin(freq * t)
    elif input_type == "ramp":
        slope = float(input("Enter ramp slope: "))
        return slope * t
    else:
        raise ValueError("Invalid input type.")

def simulate_system(plant, controller, input_signal, t):
    closed_loop = ctrl.feedback(controller * plant, 1)
    t, y = ctrl.forced_response(closed_loop, T=t, U=input_signal)
    return t, y

def main():
    print("\n--- PID Controller with Custom Plant and Inputs ---\n")
    plant = get_plant()

    print("\nChoose PID tuning method:\n1. Manual\n2. Ziegler-Nichols")
    method_choice = input("Enter 1 or 2: ").strip()
    method = "manual" if method_choice == "1" else "zn"
    controller = get_pid_controller(method)

    print("\nChoose input type:\n1. Step\n2. Pulse\n3. Sinewave\n4. Ramp")
    input_choice = input("Enter 1/2/3/4: ").strip()
    input_map = {"1": "step", "2": "pulse", "3": "sine", "4": "ramp"}
    input_type = input_map.get(input_choice, "step")

    # Time vector
    t = np.linspace(0, 30, 1000)
    input_signal = generate_input_signal(input_type, t)
    t, y = simulate_system(plant, controller, input_signal, t)

    # Plot
    plt.figure(figsize=(10, 5))
    plt.plot(t, y, label="System Output")
    plt.plot(t, input_signal, '--', label="Input Signal", alpha=0.7)
    plt.title(f"Response to {input_type.capitalize()} Input")
    plt.xlabel("Time (s)")
    plt.ylabel("Output")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
