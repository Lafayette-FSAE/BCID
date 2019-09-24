import tkinter as tk
from tkinter import ttk

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="This is a starting page", font=("Verdana", 12))
        label.pack(padx=10, pady=10)