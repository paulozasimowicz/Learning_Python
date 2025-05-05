class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint=0.0, dt=0.1):
        self.Kp = Kp          # Proportional gain
        self.Ki = Ki          # Integral gain
        self.Kd = Kd          # Derivative gain
        self.setpoint = setpoint
        self.dt = dt          # Time step

        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, measured_value):
        error = self.setpoint - measured_value
        self.integral += error * self.dt
        derivative = (error - self.prev_error) / self.dt

        output = (
            self.Kp * error +
            self.Ki * self.integral +
            self.Kd * derivative
        )

        self.prev_error = error
        return output

# Example usage
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    pid = PIDController(Kp=1.2, Ki=0.5, Kd=0.05, setpoint=10.0, dt=0.1)
    measured_value = 0.0
    values = []

    for _ in range(100):
        control_signal = pid.update(measured_value)
        measured_value += control_signal * 0.1  # Simulated system response
        values.append(measured_value)

    plt.plot(values)
    plt.axhline(pid.setpoint, color='r', linestyle='--', label="Setpoint")
    plt.title("PID Controller Response")
    plt.xlabel("Time step")
    plt.ylabel("Measured Value")
    plt.legend()
    plt.grid(True)
    plt.show()
