# Lambda Expressions: Lambda expressions are functions without a name that are quick to create and use. 
# They are written in just one line using the lambda keyword and are often used for small, simple tasks.
# Lambda expressions perform a single operation and return a result. They are defined using the lambda keyword,
#  followed by its arguments, a colon, and the expression to perform.
# You can provide arguments to lambda expressions on-the-fly by adding them in parentheses immediately after the lambda function.
#  The lambda expression should be also enclosed in parentheses.

res = (lambda x,y:x + y)(2,3)
print (res)

# The power of lambda is better shown when you use them as an anonymous function inside another function. 
# Say you have a function definition that takes one argument, and that argument will be multiplied with an unknown number:

def mult(n):
    return lambda a : a * n

double = mult(2)
triple = mult(3)

print(double(5))
print(triple(5))

# The map() function applies a specified function to every element in an iterable, like lists or tuples.
#  It produces a result that can be transformed into a list using the list() function for easy viewing or further use.

def total(numbers):
    result = 0
    # iterating over the list
    for i in numbers:
        result+=i
    return result
nums = [1,2,3,4,5]
print(total(nums))

def total(*args):
    result = 0
    for arg in args:
        result+=arg
    return result
print(total(1,2,3,4))
print(total(1,2,3,4,5,6,7))
print(total(1,2,3,4,5,6,7,8))

#kwarg is a dictionary
def display_info(**kwargs):
    #kwargs.items() return the key:valie pairs
    for key, value in kwargs.items():
        print(key,":",value)
display_info(name="Alice",age="30",city="New York")