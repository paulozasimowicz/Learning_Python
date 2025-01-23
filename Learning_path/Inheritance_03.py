# You can define methods with the same name in both parent 
# and child classes, but they can perform different operations.
#  This is known as method overriding. For instance, consider
#  the Animal class with a sound method. The Dog and Cat child 
# classes inherit the sound method from Animal but override it 
# to suit their specific needs.

# Perent Class
class Animal:
    def __init__(self, name):
        self.name = name

    # Generic sound method for any animal
    def sound(self):
        print("Making a sound")
# Child class Dog
class Dog(Animal):
    def __init__(self, name, breed, age):
        super().__init__(name)
        self.breed = breed
        self.age = age
    # Overriden sound method for Dog
    def sound(self):
        #Call the sound method from Animal
        super().sound()
        print("Woof!")

# Child class cat
class cat(Animal):
    def __init__(self, name, breed, age):
        super().__init__(name)
        self.breed = breed
        self.age = age

    # Overridden sound method for a Cat
    def sound(self):
        print("Miau")

# Creating instances
my_dog = Dog("jax", "bulldog", 4)
my_cat = cat("lily", "gato preto", 2)

# Using overridden methods
my_dog.sound()
my_cat.sound()

# Method overriding is a demonstration of another key concept in 
# OOP - polymorphism. Polymorphism lets objects use methods in 
# their own way, even if they share the same name.In this example,
#  even though each animal in the animals list may be of a different
#  subclass, the code can call sound() on each without needing to 
# know its specific type.

animals = [my_dog, my_cat]

for animal in animals:
    animal.sound()