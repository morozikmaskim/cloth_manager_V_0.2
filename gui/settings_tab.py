import tkinter as tk
from tkinter import ttk

class SettingsTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_gui()

    def setup_gui(self):
        label = ttk.Label(self.frame, text="Раздел в разработке", font=("Arial", 14))
        label.grid(row=0, column=0, padx=20, pady=20)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
