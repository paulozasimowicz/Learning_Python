# Create an App that creates solve an math problem.

# # Import math
# import math
# 
# # Define variables
# length = 10
# width = 20
# 
# # Print length and width
# print(length, width)
# 
# # Define the function to calculate the rectangular area
# def rectangular_area(length, width):
#     area = length * width
#     return area
# 
# # Call the function and store the result in a variable
# area = rectangular_area(length, width)
# 
# # Print the calculated area
# print(area)

import tkinter as tk #Library for GraphicalUserInterface

#Function Definition
def calculate_rectangle_area(side_a,side_b):
    """ Calculates the area of a rectangle from the sides a & b"""
    
    return side_a*side_b

def on_click_calc():
    """ Function that reads the input from the users and calls the calc rectangle function & puts the result into the output field """
    side_a=entry_side_a.get()
    side_b=entry_side_b.get()
    
    try:
        side_a=float(side_a)
    except TypeError:
        print("Please Enter a valid number for Side a")
        
    except ValueError:
        print("Please Enter a valid number for Side a")
        
    side_b=float(side_b)
        
    try:
        area=calculate_rectangle_area(side_a,side_b)
    except :
        print("Could not calculate the area")
    else:
        print(side_a,side_b,area)
    
        txtvar_area.set(area)


# 1. Create the App-Container
app=tk.Tk()

# 2. Insert UI-Elements into the Container
label_side_a=tk.Label(app, text="Side a")
label_side_a.grid(row=0, column=0)

entry_side_a=tk.Entry(app) #the object entry_side_a is an tk.Entry(app)
entry_side_a.grid(row=0, column=1)

label_side_b=tk.Label(app, text="Side b")
label_side_b.grid(row=1, column=0)

entry_side_b=tk.Entry(app) #the object entry_side_a is an tk.Entry(app)
entry_side_b.grid(row=1, column=1)

label_area=tk.Label(app, text="Rectangular Area")
label_area.grid(row=2, column=0)

txtvar_area=tk.StringVar()

entry_area=tk.Entry(app,textvariable=txtvar_area)
entry_area.grid(row=2,column=1)

calculate_button=tk.Button(app, text="Calculate", command=on_click_calc)
calculate_button.grid(row=3, column=0, columnspan=2)
    
                      
# 3. Run the App
app.mainloop()

