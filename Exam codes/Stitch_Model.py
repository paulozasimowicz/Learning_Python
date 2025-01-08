# Task 05: Make a model for a stitch 

# Numpy with matplotlib.pyplot interaction to create 3D coordinate systems.

import matplotlib.pyplot as plt
import numpy as np
from vedo import Tube, show

#PLEASE SELECT DESIRED OUTPUT
#0 for 3D model, 1 for 3D plot
output = 0

# Set the input values.
# w1 for the Stitch Width long
# w2 for the distance of the stitches
# b for the Depth of the Stitch
# h for the Distance of the Points from the xz Plane
# yarn_radius for the yarn radius
# number_stitches for the number of stitches

w1= 1
w2 = 0.5
b = 0.5
h = 1
yarn_radius = 0.1
number_stitches = 5

# Create the list of points
points_list = []

# Define the construction function
last_point = np.array([0, 0, 0]) # Create a starting point.
points_list.append(last_point)

def last_elem(long_list):
    x, y, z = points_list[-1]
    return(x, y, z)

#building one loop at the time to better adjust their shape
def stitch():
    #get initial conditions
    x, y, z = last_elem(points_list)
    x = x + w1 + w2
    #defining loop points
    point_1 = np.array([x+w1, 0,-b ])
    point_2 = np.array([x+w1, h,-b ])
    point_3 = np.array([x,h,-b ])     
    point_4 = np.array([x, 0, b])
    
    points_list.extend([point_1, point_2,point_3,point_4])


for i in range(number_stitches):
     stitch()

#visual output
all_points = np.array(points_list)


if output:
    #create 3D plot
    print("creating 3D plot...")
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    x, y, z = all_points[:, 0], all_points[:, 1], all_points[:, 2]
    ax.plot(x, z, y)
    plt.axis('on')
    plt.show()
else:
    #create 3D model
    print("creating 3D model...")
    stitch_tube = Tube(all_points, r=yarn_radius, c='green')
    show(stitch_tube, axes=3).close()
    