import tkinter as tk
from tkinter import ttk, font, simpledialog, messagebox
import json
import random
import re
import os
import sys
from pymongo import MongoClient
import threading

class LabelSeparator(tk.Frame):
    def __init__(self, parent, text="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # The separator is stretched across the entire width of the frame
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(row=0, column=0, sticky="ew", pady=0)

        # The label is placed above the separator
        self.label = ttk.Label(self, text=text)
        self.label.grid(row=0, column=0)

        # Configure the frame to expand the column, allowing the separator to fill the space
        self.grid_columnconfigure(0, weight=1)

        # Adjust label placement using the 'sticky' parameter to center it
        # 'ns' means north-south, which centers the label vertically in the grid cell
        self.label.grid_configure(sticky="ns")

class FontSizeChanger(tk.Frame):
    def __init__(self, position, root, font_size=12, *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        self.root = root
        self.font_size = font_size

        # "+" button to increase font size
        increase_font_button = tk.Button(position, text="+", command=self.increase_font_size)
        increase_font_button.pack(side=tk.LEFT, padx=(10, 0), pady=10)

        # "-" button to decrease font size
        decrease_font_button = tk.Button(position, text="-", command=self.decrease_font_size)
        decrease_font_button.pack(side=tk.LEFT, padx=(0, 10), pady=10)

    def increase_font_size(self):
        if self.font_size < 30:
            self.font_size += 1
            self.update_font_size(self.root)
            self.update_window_size(enlarge=True)

    def decrease_font_size(self):
        if self.font_size > 10:
            self.font_size -= 1
            self.update_font_size(self.root)
            self.update_window_size(enlarge=False)

    def update_font_size_wrapper(self):
        self.update_font_size(self.root)

    def update_font_size(self, widget):
        new_font = font.Font(size=self.font_size)

        try:
            widget.configure(font=new_font)
        except:
            pass

        for child in widget.winfo_children():
            self.update_font_size(child)

    def update_window_size(self, enlarge):
        if enlarge:
            num = 40
        else:
            num = -40

        # Get the current size of the window
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()

        # Calculate a new height, but ensure it's within the screen's limits
        screen_height = self.root.winfo_screenheight()
        new_height = min(current_height + num, screen_height)

        # Calculate a new Width, but ensure it's within the screen's limits
        screen_width = self.root.winfo_screenwidth()
        new_width = min(current_width + num*2, screen_width)

        # Update the window size using geometry
        self.root.geometry(f"{new_width}x{new_height}")
        self.root.update()  

class RequireRewrite(tk.Frame):
    def __init__(self, position, root, allowed_values=['0','1'], *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        self.root = root
        self.allowed_values = allowed_values
        
        # Frame for Rewrite widgets
        self.rewrites_frame_base = tk.Frame(root)
        position.add(self.rewrites_frame_base, stretch="always", height=80)
        LabelSeparator(self.rewrites_frame_base, text="Rewrites").pack(fill=tk.X)


        # Entry for "requires_rewrite"
        self.requires_rewrite_frame = tk.Frame(self.rewrites_frame_base)
        self.requires_rewrite_frame.pack(fill=tk.BOTH, padx=10, pady=10)

        self.requires_rewrite_label = tk.Label(self.requires_rewrite_frame, text="Question Requires Rewrite:")
        self.requires_rewrite_label.grid(row=0, column=0, sticky='w', padx=5, pady=0)
        self.requires_rewrite_entry = tk.Entry(self.requires_rewrite_frame, width = 3)
        self.requires_rewrite_entry.grid(row=0, column=1, sticky='wn', padx=5, pady=0)
        

        self.requires_rewrite_entry.bind("<KeyRelease>", self.check_input_valid)
        self.requires_rewrite_entry.bind("<FocusIn>", self.select_text)


    def update_entry_text(self, dialog_id, turn_num, json_data):
        """
        INPUT-> the json_data with specific position (dialog_id, turn_id)
        DESC-> Updates the text inside requires_rewrite
        """
        # Clear the Entry widget
        self.requires_rewrite_entry.delete(0, tk.END)

        # Fetch and insert text into the Entry widget
        count_turns = len(json_data[dialog_id]['annotations'])
        if turn_num >= count_turns: 
            raise Exception(f"The turn is not in the annotations list, it has {count_turns}, but the turn is {turn_num}")
        
        entry_text = json_data[dialog_id]['annotations'][int(turn_num)].get('requires rewrite', '')
        if entry_text is not None and entry_text != -1:
            self.requires_rewrite_entry.insert(0, entry_text)
        
        # Select all text in the Entry widget
        self.requires_rewrite_entry.select_range(0, tk.END)
                   
    def check_input_valid(self, event=None):
        """
        DESC-> checks if whatever the annotator typed inside the entry is valid and raises a warning if not
        while also deleting what he typed to clear the unvalid input
        """
        
        # Retrieve text from an Entry widget
        new_value = self.requires_rewrite_entry.get()
        
        if self.allowed_values is None or new_value in self.allowed_values:
            return True
        
        elif new_value == '':
            return True

        else:
            self.requires_rewrite_entry.delete(0, tk.END)
            tk.messagebox.showwarning("Invalid Score", f"Invalid input '{str(new_value)}'. Allowed values are: 0 or 1")
            return False
        
    def update_json_data(self, dialog_id, turn_id, json_data):
        """
        INPUT-> the json_data with specific position (dialog_id, turn_id)
        OUTPUT-> modified json_data after updating the json data with the new value
        DESC-> This function will make a change in require_rewrite field in a specific position defined by output
        and will return the json file after modyfing the json with whatever is in the tk.entry right now
        """

        new_value = self.requires_rewrite_entry.get()
        
        if new_value == None:
            raise Exception("Require Rewrite is Null even after check_valid()")
        
        if new_value == '':
            raise Exception("Require Rewrite is '' even after check_valid()")
        

        
        json_data[dialog_id]['annotations'][turn_id]["requires rewrite"] = int(new_value)
        
        return json_data
        
    def is_empty(self):
        
        if (self.requires_rewrite_entry.get() == ''): return True
        return False

    def select_text(self, event=None):
        event.widget.select_range(0,tk.END)

class DialogFrame(tk.Frame):
    def __init__(self, position, root, *args, **kwargs):
        super().__init__(position, *args, **kwargs)
        self.root = root

      # Frame for Dialog widgets
        self.dialog_frame_base = tk.Frame(root, height=1)
        position.add(self.dialog_frame_base, stretch="always", height=200)
        LabelSeparator(self.dialog_frame_base, text="Dialog Text").pack(fill=tk.X, side=tk.TOP)

        # tk.Text for dialog
        self.dialog_text = tk.Text(self.dialog_frame_base, wrap=tk.WORD, state='disabled')
        self.dialog_text.pack(fill=tk.BOTH, padx=10, pady=10)  

    def update_dialog_text(self, new_text):
        # Enable the widget to modify text
        self.dialog_text.config(state='normal')

        # Update the text
        self.dialog_text.delete(1.0, tk.END)
        self.dialog_text.insert(tk.END, new_text)

        # Disable the widget to prevent user edits
        self.dialog_text.config(state='disabled')

    def display_dialog(self, dialog_id, turn_num, json_data):
        dialog_text_content = ""

        # Construct the dialog text content
        self.count_turns = len(json_data[dialog_id]['annotations'])

        for index, dialog in enumerate(json_data[dialog_id]['dialog']):
            if index <= turn_num + 1:
                # Format each turn
                turn_text = f"Turn {dialog['turn_num'] - 1}:\n"
                turn_text += f"Q: {dialog['original_question']}\n"
                if index != turn_num + 1:
                    turn_text += f"A: {dialog['answer']}\n"
                turn_text += "-" * 40 + "\n"  # S1eparator line

                # Append this turn's text to the dialog text content
                dialog_text_content += turn_text 

        # Update the dialog text widget using the new method
        self.update_dialog_text(dialog_text_content)

        # Scroll to the end of the dialog text
        self.dialog_text.see(tk.END)

class ProgressIndicator():
    def __init__(self, position):

        # Current dialog and turn labels
        self.current_dialog_label = tk.Label(position, text="")
        self.current_dialog_label.pack(side=tk.LEFT, padx=10, pady=10)

        self.current_turn_label = tk.Label(position, text="")
        self.current_turn_label.pack(side=tk.LEFT, padx=10, pady=10)

        
    def update_current_turn_dialog_labels(self, dialog_num, turn_num, json_data, count_turns):
        # Update labels with current dialog and turn information
        self.current_dialog_label.config(text=f"Dialog: {dialog_num + 1}/{len(json_data)}")
        self.current_turn_label.config(text=f"Turn: {turn_num + 1}/{count_turns}")
    
class AnnotatorId():
    def __init__(self, position, root):
        self.annotator_id = ''
        self.root = root
        # "Update annotator_id" button on the right side
        self.update_id_button = tk.Button(position, text="Update Full Name")
        self.update_id_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def handle_annotatorId(self, json_data):
        first_dialog_id = next(iter(json_data))  # Get the first key in the JSON data
        if 'annotator_id' not in json_data[first_dialog_id] or json_data[first_dialog_id]['annotator_id'] is None or json_data[first_dialog_id]['annotator_id'] == '':
            json_data = self.update_annotator_id_dialog(json_data)
        return json_data
            
    def annotator_id_empty(self, json_data):
        first_dialog_id = next(iter(json_data))  # Get the first key in the JSON data
        if 'annotator_id' not in json_data[first_dialog_id] or json_data[first_dialog_id]['annotator_id'] is None:
            return True
        return False
    
    def update_annotator_id_dialog(self,json_data):
        first_dialog_id = next(iter(json_data))  # Get the first key in the JSON data
        current_id = json_data[first_dialog_id].get('annotator_id')  # Get current annotator_id

        new_id = simpledialog.askstring("Input", "Enter annotator's *full* name:", initialvalue=current_id, parent=self.root)
        if new_id is None: 
                self.root.destroy()
                return
        
        def contains_english_letter(s):
            if s is None:
                return False
            return bool(re.search('[a-zA-Z]', s))
        
        if contains_english_letter(new_id):
            self.annotator_id = new_id
            print(f"the new annotator is {self.annotator_id}")
            json_data = self.update_annotator_id(json_data)
            return json_data
        
        else:
            json_data = self.update_annotator_id_dialog(json_data)
            return json_data

             
    def update_annotator_id(self, json_data):
        for dialog_id in json_data:
            json_data[dialog_id]['annotator_id'] = self.annotator_id

        self.annotator_id = self.annotator_id
        return json_data
    
class MongoData():
    def __init__(self, root, connection_string):
        self.client = MongoClient(connection_string)
        self.username = None
        self.batch_id = None
        self.root = root
        self.sign_in()
        self.json_data = self.load_json()
    
    def sign_in(self):
            username = simpledialog.askstring("Input", "Please sign in", parent=self.root)
            if username is None: 
                self.root.destroy()
                return
            db = self.client.require_rewrite
            collection = db.annotators
            query = {"username": username}
            result = collection.find_one(query)
            if result != None:
                self.username = username
                self.batch_id = result['batches_order'][result['batch_id_list_index']]
                return
            else:
                messagebox.showerror("Error", "username doesn't exist, please try again. (if you dont know your username ask Ori)")
                self.sign_in()

    def next_batch(self):
        db = self.client.require_rewrite
        collection = db.annotators
        query = {"username": self.username}
        update = {"$inc": {"batch_id_list_index": 1}}  # Increment batch_id_list_index by 1

        result = collection.update_one(query, update)

        if result.matched_count > 0:
            print(f"User {self.username}'s batch_id_list_index increased by 1.")
        else:
            print("Username doesn't exist.")

             

    def load_json(self):
        data = None
        db = self.client.require_rewrite
        collection = db.json_annotations
        query = { "batch_id": self.batch_id, "username": self.username}
        result = collection.find_one(query)
        if result != None:
                print(' you already started')
                data = result['json_string']
        else:
            query = {'batch_id': self.batch_id}
            collection = db.json_batches
            result = collection.find_one(query)
            data = result['json_string']
        
        # Shuffling and storing rewrites
        self.shuffled_rewrites = {}
        self.identical_rewrites = {}
        for dialog_id, dialog_data in data.items():
            
            for turn_id, turn_data in dialog_data.items():
                # Check if turn_id is a digit
                if turn_id.isdigit():

                    # Select keys that contain 'rewrite' and do not contain 'annotator'
                    rewrites = []
                    
                    for key, value in turn_data.items():
                        if isinstance(value, dict) and 'score' in value.keys() and 'optimal' in value.keys():
                            exist = False
                            for rewrite in rewrites:
                                if value['text'] == rewrite[1]['text']:
                                    self.identical_rewrites[(dialog_id, turn_id, rewrite[0])].append(key)
                                    exist = True
                                    
                            if not exist:
                                rewrites.append((key,value))
                                self.identical_rewrites[(dialog_id, turn_id, key)] = []
                            
                    
                    random.shuffle(rewrites)
                    self.shuffled_rewrites[(dialog_id, turn_id)] = rewrites
        return data

    def save_json(self):
        # Wrap the save_json logic in a method that can be run in a thread
        thread = threading.Thread(target=self.save)
        thread.start()
        # Optionally, you can join the thread if you need to wait for it to finish
        # thread.join()

    def save(self):
        db = self.client.require_rewrite
        collection = db.json_annotations
        query = {'username': self.username, 'batch_id': self.batch_id}
        my_values = {"$set": {'username': self.username, 'batch_id': self.batch_id, 'json_string': self.json_data}}
        update_result = collection.update_one(query, my_values, upsert=True)
        if update_result.matched_count > 0:
            print(f"Document with annotator_id: {self.username} and batch_id: {self.batch_id} updated.")
        elif update_result.upserted_id is not None:
            print(f"New document inserted with id {update_result.upserted_id}.")
        else:
            print("No changes made to the database.")


class JsonData():
    def __init__(self, root):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)

        else:
            application_path = ''
        
        self.filename = os.path.join(application_path, 'target.json')
        self.root = root
        self.json_data = self.load_json()

    def load_json(self):
        data = None
        try:
            with open(self.filename, 'r') as file:
                data = json.load(file)

        except FileNotFoundError:
            tk.messagebox.showerror("Annotation File Not Found", f"Please place target.json inside the same folder with the program")
            self.root.destroy()
            

        # Shuffling and storing rewrites
        self.shuffled_rewrites = {}
        self.identical_rewrites = {}
        for dialog_id, dialog_data in data.items():
            
            for turn_id, turn_data in dialog_data.items():
                # Check if turn_id is a digit
                if turn_id.isdigit():

                    # Select keys that contain 'rewrite' and do not contain 'annotator'
                    rewrites = []
                    
                    for key, value in turn_data.items():
                        if isinstance(value, dict) and 'score' in value.keys() and 'optimal' in value.keys():
                            exist = False
                            for rewrite in rewrites:
                                if value['text'] == rewrite[1]['text']:
                                    self.identical_rewrites[(dialog_id, turn_id, rewrite[0])].append(key)
                                    exist = True
                                    
                            if not exist:
                                rewrites.append((key,value))
                                self.identical_rewrites[(dialog_id, turn_id, key)] = []
                            
                    
                    random.shuffle(rewrites)
                    self.shuffled_rewrites[(dialog_id, turn_id)] = rewrites
        return data
 
    def save_json(self):
        # Write the updated json_data back to the file
        with open(self.filename, 'w') as file:
            json.dump(self.json_data, file, indent=4)
            

class JsonViewerApp:

    def __init__(self, root, ):
        
        # Main windows settings
        self.root = root
        self.root.title("OneAI ReWrite Annotation Software")  

        # Set the minimum size of the window
        root.minsize(1000, 600)
        self.root.update()
        self.fields_check = True
        self.disable_copy = True
        self.online = False
                                          
        # Create a Top Panel Frame for options
        top_panel_frame = tk.Frame(root)
        top_panel_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Create Main PanedWindow
        main_pane = tk.PanedWindow(root, orient=tk.VERTICAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
      
        # "<" (Previous) and ">" (Next) buttons next to each other
        prev_button = tk.Button(top_panel_frame, text="<", command=self.prev_turn)
        prev_button.pack(side=tk.LEFT, padx=(10, 0), pady=10)

        next_button = tk.Button(top_panel_frame, text=">", command=self.next_turn)
        next_button.pack(side=tk.LEFT)
        
        # "<<" (Previous Dialog) and ">>" (Next Dialog) buttons
        prev_dialog_button = tk.Button(top_panel_frame, text="<<", command=self.prev_dialog)
        prev_dialog_button.pack(side=tk.LEFT, padx=(10, 0), pady=10)

        next_dialog_button = tk.Button(top_panel_frame, text=">>", command=self.next_dialog)
        next_dialog_button.pack(side=tk.LEFT)
        
        # Key bindings for arrow keys
        root.bind("<KeyRelease-Down>", self.next_focus)
        root.bind("<KeyRelease-Up>", self.back_focus)

        # Disable Copy Paste 
        if self.disable_copy == True:
            root.event_delete('<<Paste>>', '<Control-v>')
            root.event_delete('<<Copy>>', '<Control-c>')
        
        # Save Button at the bottom
        self.save_button = tk.Button(root, text="Save and Next", command=self.next_turn)
        self.save_button.pack(side=tk.BOTTOM, pady=10)
        self.save_button.bind("<Return>", self.next_turn)


        #Init all the items in the program
        self.data = None
        if self.online == False: 
            self.data = JsonData(self.root)
            
        else:
            connection_string = "mongodb+srv://orik:Ori121322@cluster0.tyiy3mk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            self.data = MongoData(self.root, connection_string)

        self.progress = ProgressIndicator(top_panel_frame)
        self.dialog_frame = DialogFrame(main_pane, root)
        self.font = FontSizeChanger(top_panel_frame, root)
        self.require_rewrite = RequireRewrite(main_pane, root)
        self.annotator_id = AnnotatorId(top_panel_frame, root)
        self.annotator_id.update_id_button.config(command=lambda: self.annotator_id.update_annotator_id_dialog(self.data.json_data))

        

        # Load JSON and display data
        self.current_dialog_num = -1
        self.current_turn_num = -1

        self.focus_list = []
        self.focus_index = 0
        self.first_focus_action = None

        if(self.data.json_data == None or self.data.json_data == ''):
            raise Exception(f"The json files is Null.\n JSON={self.data.json_data}")
      
        self.data.json_data = self.annotator_id.handle_annotatorId(self.data.json_data)
        
        # After loading JSON data, find the first turn with an empty score
        self.find_next_unscored_turn()
        self.init_turn()
        
        self.font.increase_font_size()
        self.focused_element = None

    def find_next_unscored_turn(self):
        for dialog_index, dialog_id in enumerate(self.data.json_data):
            annotations = self.data.json_data[dialog_id]['annotations']
            for turn_id in range(len(annotations)):
                turn_data = annotations[turn_id]['requires rewrite']
                if (turn_data == None):
                    self.current_dialog_num = dialog_index
                    self.current_turn_num = turn_id
                    return
    
    def are_all_fields_filled(self):
        missing_fields = []

        # Check if annotator_id is filled
        first_dialog_id = next(iter(self.data.json_data))  
        if not self.data.json_data[first_dialog_id].get('annotator_id'):
            missing_fields.append("annotator name")

        # Check if annotator rewrite is filled
        dialog_id = self.current_dialog_id()
        turn_id = self.current_turn_id()
        
        if self.require_rewrite.is_empty():
            missing_fields.append("Requires Rewrite")
                  

        if missing_fields and self.fields_check:
            return False, "The following fields are missing: " + ", ".join(missing_fields) + ". Please fill them in before proceeding."
        
        return True, ""
    
    def update_json(self):
        self.data.json_data = self.require_rewrite.update_json_data(self.current_dialog_id(), self.current_turn_id(), self.data.json_data)
            
        # Save current state and move to next if all fields are filled
        self.data.save_json()

    def current_dialog_id(self):
        return list(self.data.json_data.keys())[self.current_dialog_num]

    def current_turn_id(self):
        return int(self.current_turn_num)
    
    def init_turn(self):
        
        self.progress.update_current_turn_dialog_labels(self.current_dialog_num, self.current_turn_num, self.data.json_data, len(self.data.json_data[self.current_dialog_id()]['annotations']))
        self.dialog_frame.display_dialog(self.current_dialog_id(), self.current_turn_id(), self.data.json_data)
        self.require_rewrite.update_entry_text(self.current_dialog_id(), self.current_turn_id(), self.data.json_data)  
        self.create_focus_list()               

    def prev_turn(self):
        
        
        if self.current_turn_num > 0:
            self.current_turn_num -= 1
        else:
            if self.current_dialog_num > 0:
                self.current_dialog_num -= 1
                dialog_id = self.current_dialog_id()
                dialog_data = self.data.json_data[dialog_id]
                self.current_turn_num = dialog_data['number_of_turns'] - 2
            else:
                return  # Do nothing if already at the first dialog and turn
            
        self.progress.update_current_turn_dialog_labels(self.current_dialog_num, self.current_turn_num, self.data.json_data, len(self.data.json_data[self.current_dialog_id()]['annotations']))

        self.init_turn()

        self.font.update_font_size_wrapper()

    def next_turn(self, event=None):
        
        are_filled, message = self.are_all_fields_filled()
        if not are_filled:
            tk.messagebox.showwarning("Warning", message)
            return
        
        self.update_json()

        # Proceed to next turn if all fields are filled
        if self.current_turn_num < len(self.data.json_data[self.current_dialog_id()]['annotations']) - 1:
            self.current_turn_num += 1
        else:
            if self.current_dialog_num< len(self.data.json_data) - 1:
                self.data.next_batch()
                self.current_dialog_num += 1
                self.current_turn_num = 0
                print(f"dialog= {self.current_dialog_id()}")
            else:
                print("finished annotation file")
                return  # Do nothing if already at the last dialog and turn
            
        self.progress.update_current_turn_dialog_labels(self.current_dialog_num, self.current_turn_num, self.data.json_data, len(self.data.json_data[self.current_dialog_id()]['annotations']))

        self.init_turn()

        self.font.update_font_size_wrapper()
        
    def prev_dialog(self):
       
        if self.current_dialog_num > 0:
                self.update_json()
                self.current_dialog_num -= 1
                self.current_turn_num = 0
                self.init_turn()
                self.font.update_font_size_wrapper()
        else:
            tk.messagebox.showwarning("Warning", "This is the first dialog")

    def next_dialog(self):
      
        if self.current_dialog_num < len(self.data.json_data) - 1:
            if self.fields_check:
                if self.are_all_turns_filled(self.current_dialog_num):
                    self.update_json()
                    self.current_dialog_num += 1
                    self.current_turn_num = 0
                    self.init_turn()
                    self.font.update_font_size_wrapper()
                else:
                    tk.messagebox.showwarning("Warning", "Not all turns in this dialog are filled")
            else:
                self.update_json()
                self.current_dialog_num += 1
                self.current_turn_num = 0
                self.init_turn()
                self.font.update_font_size_wrapper()

    def are_all_turns_filled(self, dialog_index):
        dialog_id = list(self.data.json_data.keys())[dialog_index]
        dialog_data = self.data.json_data[dialog_id]
        for turn_id in range(1+0, dialog_data['number_of_turns']+1):
            turn_data = dialog_data[str(turn_id)]
            if (turn_data['requires rewrite'] == None): return False
        return True
    
    
     #add another option for showing the rewrites
        
    def create_focus_list(self):
            self.focus_list = []
            self.focus_index = 0
            self.first_focus_action = True
            self.focus_list.append(self.require_rewrite.requires_rewrite_entry)
            
            self.focus_list.append(self.save_button)
    
    def next_focus(self, event=None):
        if self.first_focus_action:
            self.first_focus_action = False
        else:
            self.focus_index += 1

        if self.focus_index >= len(self.focus_list):
            self.focus_index = 0

        try:
            self.focus_list[self.focus_index].focus()
        except:
            raise Exception(f"Problem with foccused occured: focus_index is {self.focus_index} but the len of focus list is {str(len(self.focus_list))}")

    def back_focus(self, event=None):
        if self.first_focus_action:
            self.focus_index = len(self.focus_list)  # Start from the end
            self.first_focus_action = False

        self.focus_index -= 1
        if self.focus_index < 0:
            self.focus_index = len(self.focus_list) - 1

        self.focus_list[self.focus_index].focus()

def main():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)

    else:
        application_path = ''

    target_path = os.path.join(application_path, 'target.json')

    # Check if the file exists
    if not os.path.isfile(target_path):
        tk.messagebox.showerror("Annotation File Not Found", "Please place target.json inside the same folder with the program")

        return


    root = tk.Tk()
    app = JsonViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

