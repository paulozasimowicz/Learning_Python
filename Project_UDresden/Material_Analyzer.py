# TUD - Dresden University of Technology

# Project: Material Analyzer for calculation of drape coefficient and other properties.

# Author: Paulo Vitor Zasimowicz Pinto Calaca

# Date: 04.03.2025

# Version: 1.0

# Importing necessary libraries
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.ttk import Button
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk, UnidentifiedImageError
import cv2
import numpy as np

def process_with_opencv(image):
    # Convert PIL Image to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # Example OpenCV operations (you can modify these as needed)
    # Convert to grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Convert back to PIL Image
    return Image.fromarray(cv2.cvtColor(blurred, cv2.COLOR_GRAY2RGB))

def upload_action():
   try: 
        img_pack = askopenfilename()
        im = Image.open(img_pack)
        img_width, img_height = im.size

        if img_width > WIDTH or img_height > HEIGHT:
            while img_width > WIDTH or img_height > HEIGHT:
                img_width *= .99
                img_height *= .99

            im = im.resize((int(img_width), int(img_height)))
            messagebox.showinfo(title='Warning', message='Image was resized to fit the screen')
        
        # Process with OpenCV
        global processed_image
        processed_image = process_with_opencv(im)
        
        # Convert to grayscale for display
        gray_image = processed_image.convert("L")
        img = ImageTk.PhotoImage(gray_image)
        canvas.img = img
        canvas.create_image(WIDTH/2,HEIGHT/2, image=img, anchor=tk.CENTER)
   except UnidentifiedImageError:
       messagebox.showinfo(title= 'Upload Error',
                           message= 'Image could not be read, please make sure the selected is an image file')

def save_action():
    try:
        #Check if there's an image to save
        if not hasattr(canvas,'img'):
            messagebox.showinfo(title='Save error', message='No image to save. Please upload image first')
            return
        
        filename = filedialog.asksaveasfilename(defaultextension=".png", 
                                               filetypes=[("PNG files","*.png"),
                                                         ("JPEG files", "*.jpg"),
                                                         ("All files","*.*")])
        if filename:
            # Save the processed grayscale image
            processed_image.save(filename)
            messagebox.showinfo(title='Success', message='Image saved successfully!')
    except Exception as e:
        messagebox.showerror(title='Save Error', message=f'Error saving image: {str(e)}')



if __name__ == "__main__":

    WIDTH,HEIGHT = 1024,720

    window = tk.Tk()
    window.title("Material Analyzer")
    window.geometry('%sx%s' % (WIDTH,HEIGHT))

    canvas = tk.Canvas(window, width=WIDTH, height=HEIGHT-50, bg="white")
    canvas.pack()

    # Create a frame to hold the buttons
    button_frame = tk.Frame(window)
    button_frame.pack(side='top',pady=10)

    # Add Upload and Save buttons

    upload_btn = tk.Button(button_frame,text='Upload' , command=lambda:upload_action())
    upload_btn.pack(side='left', padx=5)

    save_btn = tk.Button(button_frame, text='Save', command=lambda:save_action())
    save_btn.pack(side='left', padx=5)

    window.mainloop()

