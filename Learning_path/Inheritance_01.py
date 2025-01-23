# Inheritance is a key concept for situations where you have 
# an existing class with defined attributes and behaviors,
#  and you need a new class that not only shares these 
# characteristics but also has its own unique ones. 
# Inheritance allows the new class to 'inherit' properties 
# from the existing class while adding or modifying specific 
# features as needed.

class Animal:
    def __init__(self,name):
        self.name = name

    def move(self):
        print("Moving")

# Inherits from Animal class
class Dog(Animal):
    # Specific behavior
    def bark(self):
        print("woof!")

# Creating an instance
my_dog = Dog("Bob")

# Inherited attribute and behavior
print(my_dog.name)
my_dog.move()

#Specific behavior
my_dog.bark()