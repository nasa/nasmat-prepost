"""Simple code to run MAC files to verify input file reading works"""
import sys
import os
import tkinter as tk
from tkinter import filedialog
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mac_inp import mac_inp #pylint: disable=C0413



RUN_ALL_IN_DIR = True


root = tk.Tk()
root.withdraw()
run_directory = filedialog.askdirectory()

if RUN_ALL_IN_DIR:
    mac_files = [os.path.join(run_directory, f)
                for f in os.listdir(run_directory) if f.upper().endswith('.MAC')]
    ECHO=False
else:
    mac_files=[os.path.join(run_directory, 'TEST13.MAC')]
    ECHO=True


for file in mac_files:

    if RUN_ALL_IN_DIR:
        try:
            mac=mac_inp(file,echo=ECHO)
        except Exception as e: #pylint: disable=W0718
            print(f"Error reading file {file}: {e}")
    else:
        mac=mac_inp(file,echo=ECHO)
