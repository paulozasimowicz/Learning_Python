# TypeError and try function.
side_a="2"
side_b="we@"

def calculate_rectangle_area(side_a,side_b):
    """Calculates the area of a rectangle from the sides a & b"""
    
    return side_a*side_b

try:
    area=calculate_rectangle_area(side_a,side_b)
    print(f"The Rectangle with the sides {side_a} and {side_b} has the area {area}.")

except TypeError:
        print("Please only enter numbers :) ")
except:
    print("There was a problem (taht i could not think of happening) : ( ")
    
print("Finished")