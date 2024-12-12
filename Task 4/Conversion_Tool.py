# Create  a Conversion Tool of Denier to Tex. The input is a Denier number and the output is a Tex Number.

#Library for GraphicalUserInterface
import tkinter as tk
from tkinter import PhotoImage
from PIL import Image, ImageTk
import platform
import subprocess

# Function to play the song
music_process = None  # Global variable to track the subprocess

def play_song(file_path):
    """Plays a song using subprocess."""
    global music_process
    current_os = platform.system()

    if current_os == "Darwin":  # macOS
        music_process = subprocess.Popen(["afplay", file_path])
    elif current_os == "Windows":  # Windows
        music_process = subprocess.Popen(["wmplayer", file_path], shell=True)
    elif current_os == "Linux":  # Linux
        music_process = subprocess.Popen(["mpg123", file_path])
    else:
        print("Unsupported operating system.")

# Function to stop the song
def stop_song():
    """Stops the music playback if the process is running."""
    global music_process
    if music_process is not None:
        music_process.terminate()
        music_process = None

# Define the function to solve our problem

def convert_denier_to_tex (denier_number):
    """ Convert the Denier Number to Tex number."""
    if denier_number>0: # I put an If elif to already set that the number should be > than 0.
        return denier_number/9
    elif TypeError:
        print("Please enter a value above 0.")

def on_click_convert():
    """ Function that reads the input from the users and calls the conversion function & puts the result into the output field """
    denier_number=entry_denier_number.get()
    
    try:
        denier_number=float(denier_number)
    except TypeError:
        print("Please enter a valid number for Denier")
    except ValueError:
        print("Please enter a valid number for Denier")
        
    try:
        tex_number=convert_denier_to_tex(denier_number)
    except :
        print("Could not convert Denier number to Tex")
    else:
        print(denier_number,tex_number)
    
        txtvar_tex_number.set(tex_number)
        
# 1. Create the App-Container for the conversion
app=tk.Tk()
app.title("Denier to Tex Converter")
app.geometry("500x300")  # Match the window size to the image

play_song("music_brazil.mp3") #play the music background

# Load and display the background image
background_image = Image.open("brazil_background.jpg")  # I put the image that I want
background_image = background_image.resize((500, 300))  # The resize is to match the window size
bg_image = ImageTk.PhotoImage(background_image) # Says, okay this is the bg_image, save it.

# Create a canvas and place the background image
canvas = tk.Canvas(app, width=500, height=300) #create the canvas in the app
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_image, anchor="nw") # select which image you want and anchor in the app 

# 2. Insert UI-Elements into the Container
label_denier_number = tk.Label(app, text="Denier Number", bg="black") # Add UI elements on top of the canvas
canvas.create_window(200, 50, window=label_denier_number) # Create the window for the Denier number

entry_denier_number = tk.Entry(app) # create the box to the user enter the text/number
canvas.create_window(350, 50, window=entry_denier_number) # set the place of the box

label_tex_number = tk.Label(app, text="Tex Number", bg="black")
canvas.create_window(200, 100, window=label_tex_number) # set the place of the box

txtvar_tex_number = tk.StringVar()

entry_tex_number = tk.Entry(app, textvariable=txtvar_tex_number)
canvas.create_window(350, 100, window=entry_tex_number) # set the place of the box

convert_button = tk.Button(app, text="Convert Denier to Tex", command=on_click_convert)
canvas.create_window(300, 150, window=convert_button) # set the place of the box
    
# Bind the app's close event to stop the music
app.protocol("WM_DELETE_WINDOW", lambda: (stop_song(), app.destroy()))

# 3. Run the App
app.mainloop()

        