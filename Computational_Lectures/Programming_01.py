# First's interaction with Python, print, type, sum, substracted, divided, exp, root, functions, list, for.

Hello = "235246"

print(Hello)


Hello = "Hi, this is a Hello Message."

print(Hello)


text="Hi!"
number=1
number_float= 0.5

print(text)
print(number)

print(text, type(text))
print(number, type(number))
print(number_float, type(number_float))

added = number + number_float

print(added, type(number+number_float))

subtracted = number - number_float

print(subtracted, type(subtracted))

multiplied = added * subtracted

print(multiplied, type(multiplied))

divided=multiplied/2
print(divided, type(divided))

exp=4**2
print(exp)

root=exp**0.5
print(root, type(root))

root = int(root)
print(root, type(root))

number = 0.7
print(number, type(number))
rounded_number = round(1.7)
print(rounded_number, type(rounded_number))

message="You are late by"
minutes_late = 13
units="minutes"

combined_message = message + str(minutes_late) + units

print(f"You are late by {minutes_late} minutes!")
print(f"{message} {minutes_late} {units}")

number_1=20

print(number_1/2 +10)

number_2=3.7

print(number_2/2 +10)

number_3=89

print(number_3/2 +10)

# FUNCTION DEFINITION

def divide_and_add(number):
    '''
    Divides by 2 and then adds 10,
    '''
    
    divided=number/2
    divided_and_added = divided + 10
    print(divided_and_added)

# CALLING THE FUNCTION
divide_and_add(number_1)
divide_and_add(number_2)

the_list=[3.6,7,28.1234567,90]

print(the_list)

the_list.append((42))
print(the_list)
the_list.remove(7)
print(the_list)

the_list.pop(-2)
print(the_list)


the_list.append([5,4,3,2,1])
print(the_list)

print("Code with function")

def divide_and_add(number):
    '''
    Divides by 2 and then adds 10,
    '''
    divided=number/2
    divided_and_added = divided + 10
    return(divided_and_added)
    
the_list=[3.6,7,28.1234567,90]

for number in the_list:
    result=divide_and_add(number)
    print(result)





