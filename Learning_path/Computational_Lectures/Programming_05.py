# Plot a sin plot.

import math
import matplotlib.pyplot as plt

x_list=list(range(100))

print(x_list[0:10]) #print first 10 values of x_list

x_list=[x/10 for x in x_list]

print(x_list[0:10]) #print first 10 values of x_list

y_list=[math.sin(x) for x in x_list]

fig=plt.figure()
fig.suptitle("A sin plot")

plt.plot(x_list,y_list)
plt.show()

