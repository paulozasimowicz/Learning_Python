# First steps with Numpy.

import numpy as np

# Create an array

row_1=[1,2,3,4]
row_2=[4,3,2,1]

array_list=[row_1,row_2]

print(array_list,type(array_list))

array= np.array(array_list)

print(array,type(array))

multiplied_array = np.multiply(array, 5)

print(multiplied_array)

add_array = np.add(array,5)

print(add_array)

sub_array=np.subtract(array,5)

print(sub_array)

divide_array=np.divide(array,5)

print(divide_array)

exp_array=np.power(array,5)

print(exp_array)

mod_array=np.mod(array,5)

print(mod_array)

array_2=np.array([[5,5,5,5],[9,8,7,6]])

multiplied_array = np.multiply(array, array_2)

print(multiplied_array)

add_array = np.add(array,array_2)

print(add_array)

sub_array=np.subtract(array,array_2)

print(sub_array)

divide_array=np.divide(array,array_2)

print(divide_array)

exp_array=np.power(array,array_2)

print(exp_array)

mod_array=np.mod(array,array_2)

print(mod_array)

array_3=([3,4,5,5],[2,2,4,2])

t_array=np.transpose(array_3)
print(t_array)