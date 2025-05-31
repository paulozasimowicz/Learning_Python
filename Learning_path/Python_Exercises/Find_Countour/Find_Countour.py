# Find_Countour
#This code is used to find the contour of the image
#It uses the cv2 library to load the image
#It uses the numpy library to create the kernel
#It uses the cv2 library to find the contours
#It uses the cv2 library to draw the contours
#It uses the cv2 library to display the image
#It uses the cv2 library to save the image
#It uses the cv2 library to close the image

import cv2
import numpy as np

# Load the image
img = cv2.imread("/Users/paulovitor/Desktop/WE-TEAM/Github_edit/Learning_Python/Learning_path/Python_Exercises/Find_Countour/fisch2-cut.png", cv2.IMREAD_GRAYSCALE)
if img is None:
    print("❌ Image not found.")
    exit()

# Threshold to binary (assume dark object on white background)
_, binary = cv2.threshold(img, 250, 255, cv2.THRESH_BINARY_INV)

# Erode and dilate to clean up noise (morphological closing)
kernel = np.ones((5, 5), np.uint8)
closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

# Optional: Fill holes using flood fill
flood_filled = closed.copy()
h, w = closed.shape[:2]
mask = np.zeros((h+2, w+2), np.uint8)
cv2.floodFill(flood_filled, mask, (0, 0), 255)
filled = cv2.bitwise_not(flood_filled) | closed  # fill holes inside object

# Find contours
contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

# Draw contours and measure
output = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
for contour in contours:
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    print(f"Area: {area:.2f} px^2, Perimeter: {perimeter:.2f} px")
    cv2.drawContours(output, [contour], -1, (0, 255, 0), 2)

# Show result
cv2.imshow("Contour", output)
cv2.waitKey(0)
cv2.destroyAllWindows()
