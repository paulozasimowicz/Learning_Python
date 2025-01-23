# What if we want to not only inherit attributes but also 
# add specific ones to a child class? In this case, 
# we define an __init__ method in the child class. 
# Use super().__init__() to inherit attributes from
#  the parent class, and then define any additional
#  attributes as usual.

#parent class
class Animal():
    def __init__(self,name):
        self.name = name

    def move(self):
        print("Moving")

#child class
class Dog(Animal):
    def __init__(self, name, breed, age):
        #Initialize attributes of the superclass
        super().__init__(name)
        #Additional attributes specific to Dog
        self.breed = breed
        self.age = age
    
    def bark(self):
        print("Woof!")

my_dog = Dog("Jax","Bulldog", 5)
#inherited attribute
print(my_dog.name)

#Additional attributes
print(my_dog.breed)
print(my_dog.age)