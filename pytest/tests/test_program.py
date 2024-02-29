import pytest
import tkinter as tk
from tkinter import ttk, font, simpledialog, messagebox
import json
import random
import re
import os
import sys
from pymongo import MongoClient
import threading
import source.program as program  # Replace 'your_module' with the actual name of your Python file

@pytest.fixture
def program():

    target_path = 'target.json'

    # Check if the file exists
    if not os.path.isfile(target_path):
        tk.messagebox.showerror("Annotation File Not Found", "Please place target.json inside the same folder with the program")
        return

    root = tk.Tk()
    app = program.JsonViewerApp(root)
    root.mainloop()

def test_initial_state(program):
    frame = program
    assert frame.allowed_values == ['0', '1'], "Initial allowed values should be ['0', '1']"

@pytest.mark.parametrize("input_value,expected_result", [
    ("0", True),
    ("1", True),
    ("2", False),  # Assuming '2' is not a valid input and should result in the deletion of the input
    ("", True),    # Empty string might be allowed depending on the logic
])
def test_check_input_valid(program, input_value, expected_result):
    frame = program
    frame.requires_rewrite_entry.insert(0, input_value)
    assert frame.check_input_valid() == expected_result

def test_update_json_data_with_invalid_input(program):
    frame = program
    with pytest.raises(Exception):
        frame.update_json_data("invalid_dialog_id", 0, {})  # Test with invalid dialog_id and turn_id
