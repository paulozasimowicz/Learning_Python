# Numpy with matplotlib.pyplot interaction to create 3D coordinate systems.

import matplotlib.pyplot as plt
import numpy as np

# Create an empty 3D coordinate system
ax = plt.figure().add_subplot(projection='3d')

# Prepare arrays x, yyarn
x=[1,2,3,1,2,3]
y=[3,2,1,3,2,1]
z=[5,6,7,1,2,3]

# Ploting my coordiantes
ax.plot(x, y, z)

# Showing the plot
plt.show()