# Explain how import works, use of libraryes, exercise of calculation of areas using for...in.
import math

from math import pi


# print(math.pi)
# print(pi)
# print(piiiiiiii)


# exercise: add a function and calculate the area of circle for all values in the list
list_of_radii=[40,12,13.7777,56,5999]
list_of_areas=[] #create an empty list

def area_circle(radius):
    area= radius**2*pi
    return(area)

for radius in list_of_radii:
    area =(area_circle(radius))
    list_of_areas.append(area)

lenght_of_radius_list=len(list_of_radii)

for i in range(lenght_of_radius_list):
    radius=list_of_radii[i]
    area=list_of_areas[i]
    area=round(area,2)
    print(f"The area of a circle with the radius is {radius} is {area}")
                       