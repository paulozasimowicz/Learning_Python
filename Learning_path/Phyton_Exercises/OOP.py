# To add attributes to a class, you must define the __init__ method. 
# This method's first parameter is always self, which represents the 
# instance of the class. Following self, you specify the attributes 
# you wish to include. Then, inside the function, you assign values 
# to the initialized object's attributes, setting their initial state.

class Car:
    # Initialize attributes
    def __init__(self, brand, model, color):
        # Assign values to attributes
        self.brand = brand
        self.model = model
        self.color = color

    def honk(self):
        print('Beep beep!')
# Create an object of the Car class
my_car = Car('Audi','A3','yellow')

# Display an object of the Car class
print(my_car.brand,my_car.color)

# In addition to attributes, you can add custom behaviors to a class 
# by defining functions within it. These functions, known as methods,
#  should include the 'self' parameter to interact with the class
#  instance. You can call these methods using the dot . notation,
#  similar to how you access attributes.

my_car.honk()

#funcion
def greet():
    print("Welcome!")

#list
prices = [55,342,24,54]

#data types
x = 5
city = "london"
is_open = True

print(type(greet))
print(type(prices))
print(type(x))
print(type(city))
print(type(is_open))

