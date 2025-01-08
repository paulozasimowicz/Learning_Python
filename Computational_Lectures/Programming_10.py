# Weave program in pyton.

# Import Packages
import matplotlib.pyplot as plt
import numpy as np
import vedo

# Define Inputs
pattern=np.array([[0,1],[1,0]])

thickness=0.3

dist_weft=1
dist_warp=0.8

diam_weft=0.1
diam_warp=0.5

rep_weft=2
rep_warp=2

print(pattern)

expanded_pattern=np.tile(pattern,(rep_weft,rep_warp))
print(expanded_pattern)

print(expanded_pattern == 0)

pattern[pattern == 0] = -1
print(pattern)

# in the array "expanded_pattern" select all idices where it has
# the value of 0 and then assingn the number -1 to them
expanded_pattern[expanded_pattern == 0] = -1
print(expanded_pattern)

z_warp=np.multiply(expanded_pattern,thickness/2)
print(z_warp)

z_weft=np.multiply(z_warp,-1)
print(z_weft)

nr_weft,nr_warp = expanded_pattern.shape

x_list=list(range(nr_warp))
print(x_list)

x_array=np.tile(x_list,(nr_weft,1))

x_array=np.multiply(x_array,dist_warp)

print(x_array)

y_list=list(range(nr_weft))

y_array=np.tile(x_list,(nr_warp,1))

y_array=np.rot90(y_array)
y_array=np.multiply(y_array,dist_weft)

# creating the actual yarns

warp_yarn_list=[]
weft_yarn_list=[]


for i in range(nr_warp):
    x=x_array[i,:]
    y=y_array[i,:]
    z=z_warp[i,:]
    
    yarn_array=np.array([x,y,z])
    
    warp_yarn_list.append(yarn_array)
    
for i in range(nr_weft):
    x=x_array[:,i]
    y=y_array[:,i]
    z=z_weft[:,i]
    
    yarn_array=np.array([x,y,z])
    
    weft_yarn_list.append(yarn_array)
    
yarn_3d=[]

for yarn in warp_yarn_list:
#     nr_of_dimensions, nr_of_points = yarn_shape #this
    nr_of_points=yarn.shape[1]  # or this
    
    points=[]
    
    for i in range(nr_of_points):
        point=yarn[:,i]
        points.append(point)
    
    yarn_line=vedo.Spline(points)
    yarn_tube =vedo.Tube(yarn_line, r=diam_warp)
    yarn_3d.append(yarn_tube)
   
for yarn in weft_yarn_list:
#     nr_of_dimensions, nr_of_points = yarn_shape #this
    nr_of_points=yarn.shape[1]  # or this
    
    points=[]
    
    for i in range(nr_of_points):
        point=yarn[:,i]
        points.append(point)
    
    yarn_line=vedo.Spline(points)
    yarn_tube =vedo.Tube(yarn_line, r=diam_weft)
    yarn_3d.append(yarn_tube)

vedo.show(yarn_3d, axes=9).close()   

    
    
    
    
# Create an empty 3D coordinate system
ax = plt.figure().add_subplot(projection='3d')

# Prepare arrays x, yyarn
for yarn in yarn_list:
    
    print(yarn)
    
    print("----------")
    
    x=yarn[0,:]
    y=yarn[1,:]
    z=yarn[2,:]
    
    # Ploting my coordiantes
    ax.plot(x, y, z)


# Showing the plot
ax.set_xlabel("WARP")
ax.set_ylabel("WEFT")
ax.set_zlabel("THICKNESS")


plt.show()