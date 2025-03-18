# TUD - Dresden University of Technology

# Project: Material Analyzer for calculation of drape coefficient and other properties.

# Author: Paulo Vitor Zasimowicz Pinto Calaca

# Date: 04.03.2025

# Version: 1.0

# Importing necessary libraries
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Button
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk, UnidentifiedImageError


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
        # Convert to grayscale
        gray_image = im.convert("L")
        img = ImageTk.PhotoImage(gray_image)
        canvas.img = img
        canvas.create_image(WIDTH/2,HEIGHT/2, image=img, anchor=tk.CENTER)
   except UnidentifiedImageError:
       messagebox.showinfo(title= 'Upload Error',
                           message= 'Image could not be read, please make sure the selected is an image file')




if __name__ == "__main__":

    WIDTH,HEIGHT = 1024,720

    window = tk.Tk()
    window.title("Material Analyzer")
    window.geometry('%sx%s' % (WIDTH,HEIGHT))

    canvas = tk.Canvas(window, width=WIDTH, height=HEIGHT-50, bg="white")
    canvas.pack()

    btn = tk.Button(window,text='Upload' , command=lambda:upload_action())
    btn.pack(side='top', pady=10)

    window.mainloop()

