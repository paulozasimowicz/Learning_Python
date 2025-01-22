# Using functions inside other functions. Functions can take other functions as arguments.

def welcome(name):
    return "Welcome" + name

def process_user(name, func):
    return func(name)

print(process_user("Alice",welcome))