
import cv2

# Video path
video_path = "/Users/paulovitor/Downloads/IMG_8219.MOV"

# Initial window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 500

WINDOW_NAME = "RGB + Depth Viewer"

# Open video
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    raise RuntimeError("Could not open video file.")

# Get original FPS
fps = cap.get(cv2.CAP_PROP_FPS)
if fps <= 0:
    fps = 30

frame_delay = max(1, round(1000 / fps))

# Create one resizable window
cv2.namedWindow(
    WINDOW_NAME,
    cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO
)

cv2.resizeWindow(
    WINDOW_NAME,
    WINDOW_WIDTH,
    WINDOW_HEIGHT
)

print("RGB + Depth Viewer")
print("Video loops automatically.")
print("Drag window corners to resize.")
print("Press 'q' to quit.")

while True:

    ret, frame = cap.read()

    # Restart video automatically
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()

        if not ret:
            break

    # Get video dimensions
    height, width = frame.shape[:2]
    midpoint = width // 2

    # Split RGB and Depth
    rgb_view = frame[:, :midpoint]
    depth_view = frame[:, midpoint:]

    # Convert depth to grayscale
    depth_gray = cv2.cvtColor(
        depth_view,
        cv2.COLOR_BGR2GRAY
    )

    # Apply depth colormap
    colorized_depth = cv2.applyColorMap(
        depth_gray,
        cv2.COLORMAP_JET
    )

    # Combine both streams horizontally
    combined_view = cv2.hconcat([
        rgb_view,
        colorized_depth
    ])

    # Add labels
    cv2.putText(
        combined_view,
        "RGB",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    cv2.putText(
        combined_view,
        "DEPTH",
        (midpoint + 20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    # Display combined video
    cv2.imshow(WINDOW_NAME, combined_view)

    # Quit with q
    if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
