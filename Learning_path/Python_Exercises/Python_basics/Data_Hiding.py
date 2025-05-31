# Data hiding is a key idea in making code with objects (like in games or apps) safer and cleaner. 
# It means keeping some parts of an object private so that only certain parts of your code can change them. 
# This helps prevent mistakes and keeps your code easy to manage.In this lesson, you'll explore how data hiding 
# contributes to encapsulation in OOP, enhancing the security and robustness of your code.

class Car:
    def __init__(self, model, year, odometer):
        self.model = model
        self.year = year
        # making the odometer attribute 'protected'
        self._odometer = odometer

    def describe_car(self):
        print(self.year,self.model)
    
    def read_odometer(self):
        print("Odometer:", self._odometer, "miles")

my_car = Car('Audi', 2020, 15000)

# my_car.describe_car()
# my_car.read_odometer()

# # changing a value of the attribute
# my_car.odometer = 20000

# my_car.read_odometer()

# accessing the protected attribute
print(my_car._odometer)

# The next level of data hiding involves making an attribute private. This is achieved by prefixing the attribute name with two underscores (e.g., __attribute). In this case, unlike protected attributes, this is not just a convention - it limits its access outside the class through name mangling, enhancing data protection and encapsulation. This method is used for sensitive or internal data, strongly discouraging external access.

class Car:
  def __init__(self, model, year, odometer):
    self.model = model
    self.year = year
    # Making the odometer attribute 'private'
    self.__odometer = odometer