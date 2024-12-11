# Use of matplotlib.pyplot to plot graphs, len, change colors in a graph.
import matplotlib.pyplot as plt


a_list_of_numbers=[4,6,2,10,20,-5]

print(a_list_of_numbers)

fig = plt.figure() #create empty figure

fig.suptitle("A line plot") #give it a name

plt.plot(a_list_of_numbers, marker="*", c="blue") #plot something
plt.show() #display the figure


fig = plt.figure() #create empty figure

fig.suptitle("A bar plot") #give it a name

index_list=list(
    range(
        len(a_list_of_numbers)
        )
    )
print(index_list)

plt.bar(x=index_list,height=a_list_of_numbers, color="purple")
plt.show()#Display the figure

