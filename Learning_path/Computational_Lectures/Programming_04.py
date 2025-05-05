# Exercise: show if x is an even number, use of if, else, for...in.

x_list=list(range(100))

# y_list=[]
# 
# for x in x_list:
#     y_list.append(x/2)
# 
# print(y_list)

#LIST COMPREHENSION

# y_list=[x/2 for x in x_list]
# 
# print(y_list)

y_list=[x/2 for x in x_list if x%2 == 0]
# 
# a_bool=True
# print(a_bool, type(a_bool))
# 
# another_bool=False

for i in range(6):
    
    if i%2 == 0:
        print(f"{i} is an even number")
    else:
        print(f"{i} is an odd number")
