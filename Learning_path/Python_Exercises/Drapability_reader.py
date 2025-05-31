import cv2
import numpy as np

# Constants (in cm or converted to pixels as needed)
R_SUPPORT = 18 / 2  # support disc diameter in cm / 2
R_FABRIC = 30 / 2   # fabric diameter in cm / 2

# Function to calculate area of a circle given radius in cm
def circle_area_cm2(radius_cm):
    return np.pi * (radius_cm ** 2)

# Load the image in grayscale
img = cv2.imread("/Users/paulovitor/Desktop/WE-TEAM/Github_edit/Learning_Python/Learning_path/fisch2.jpg", cv2.IMREAD_GRAYSCALE)
if img is None:
    print("❌ Error: Image not found.")
    exit()

# Threshold the image to binary (white = draped area)
_, binary = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY_INV)

# Optional: show the binary image
cv2.imshow("Thresholded", binary)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Count white pixels (i.e., draped area in image)
draped_pixel_area = cv2.countNonZero(binary)

# Convert image dimensions to real-world area
# You must calibrate this if you want real units, or work in pixels only
# For now, calculate everything in pixels and use ratios

# Calculate reference pixel areas for the fabric and support
height, width = img.shape
cx, cy = width // 2, height // 2

# Convert reference radii from cm to pixels (assume known or calibrated)
# Replace these with the correct pixel values from your image
R_FABRIC_PIX = 300  # example: full fabric radius in pixels
R_SUPPORT_PIX = 180  # example: support disc radius in pixels

area_support_pix = np.pi * (R_SUPPORT_PIX ** 2)
area_fabric_pix = np.pi * (R_FABRIC_PIX ** 2)

# Drape Coefficient formula
drape_coeff = ((draped_pixel_area - area_support_pix) /
               (area_fabric_pix - area_support_pix)) * 100

print(f"Drape area (px): {draped_pixel_area:.2f}")
print(f"Drape Coefficient: {drape_coeff:.2f} %")

