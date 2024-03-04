import tkinter as tk
from tkinter import ttk, font, simpledialog, messagebox
import json
import random
import re
import os
import sys
from pymongo import MongoClient
import threading
import traceback



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
        """increases the font size
        """
        if self.font_size < 30:
            self.font_size += 1
            self.update_font_size(self.root)
            self.update_window_size(enlarge=True)

    def decrease_font_size(self):
        """decreases the font size
        """
        if self.font_size > 10:
            self.font_size -= 1
            self.update_font_size(self.root)
            self.update_window_size(enlarge=False)

    def update_font_size_wrapper(self):
        """ Prepares to update the whole program, 
        using a recursive function that takes the root frame and updates all the child widgets
        """
        self.update_font_size(self.root)

    def update_font_size(self, widget):
        """the recursive function to update font

        Args:
            widget (object): tkinter object
        """
        new_font = font.Font(size=self.font_size)

        try:
            widget.configure(font=new_font)
        except:
            pass

        for child in widget.winfo_children():
            self.update_font_size(child)

    def update_window_size(self, enlarge):
        """updates the window size as well so the text has enough space

        Args:
            enlarge (boolean): if True, make window bigger, if False, make windows smaller
        """
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
        """checks if the requires_rewrite entry is empty

        Returns:
            Boolean: True if empty, false if not
        """
        if (self.requires_rewrite_entry.get() == ''): return True
        return False

    def select_text(self, event=None):
        """highlight all the the text when selecting the entry

        Args:
            event: usually the event when someone presses the entry
        """
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
        """gets new text amd updates the DialogFrame window.

        Args:
            new_text (string): the new text to update
        """
        # Enable the widget to modify text
        self.dialog_text.config(state='normal')

        # Update the text
        self.dialog_text.delete(1.0, tk.END)
        self.dialog_text.insert(tk.END, new_text)

        # Disable the widget to prevent user edits
        self.dialog_text.config(state='disabled')

        # Scroll to the end of the dialog text
        self.dialog_text.see(tk.END)

    def display_dialog(self, dialog_id, turn_num, json_data):
        """gets a specific dialog_id and turn_num, then formats the data from the json
        and creates the new text to insert inside the DialogFrame window.

        Args:
            dialog_id (int): the dialog to access
            turn_num (int): until what turn to create the text
            json_data (string): the json data to to use
        """

        dialog_text_content = ""

        for index, dialog in enumerate(json_data[dialog_id]['dialog']):
            if index <= turn_num + 1:
                # Format each turn
                turn_text = f"Turn {dialog['turn_num']}:\n"
                turn_text += f"Q: {dialog['original_question']}\n"
                if index != turn_num + 1:
                    turn_text += f"A: {dialog['answer']}\n"
                turn_text += "-" * 40 + "\n"  # S1eparator line

                # Append this turn's text to the dialog text content
                dialog_text_content += turn_text 

        # Update the dialog text widget using the new method
        self.update_dialog_text(dialog_text_content)

class ProgressIndicator():
    def __init__(self, position):

        # Current dialog and turn labels
        self.current_dialog_label = tk.Label(position, text="")
        self.current_dialog_label.pack(side=tk.LEFT, padx=10, pady=10)

        self.current_turn_label = tk.Label(position, text="")
        self.current_turn_label.pack(side=tk.LEFT, padx=10, pady=10)
       
    def update_current_turn_dialog_labels(self, dialog_num, turn_num, json_data, count_turns):
        """updates the indicator of where the annotator is (in what dialog and what turn)

        Args:
            dialog_num (int): the dialog the annotator is on
            turn_num (int):the turn the annotator is on
            json_data (string): the json data 
            count_turns (int): the number of turns in the dialog
        """
        #updates the dialog progress label
        self.current_dialog_label.config(text=f"Dialog: {dialog_num + 1}/{len(json_data)}")

        #updates the turn progress label
        self.current_turn_label.config(text=f"Turn: {turn_num + 1}/{count_turns}")
    
class AnnotatorId():
    def __init__(self, position, root):
        self.annotator_id = ''
        self.root = root
        # "Update annotator_id" button on the right side
        self.update_id_button = tk.Button(position, text="Update Full Name")
        self.update_id_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def handle_annotatorId(self, json_data):
        """used to check if the json_data has an annotator_name inside it, if it doesn't calls a function to ask the user for a name.

        Args:
            json_data (string): the json data being annotated

        Returns:
            string: the json_data after being updated with an annotator_name
        """
        first_dialog_id = next(iter(json_data))  # Get the first key in the JSON data
        if 'annotator_name' not in json_data[first_dialog_id] or json_data[first_dialog_id]['annotator_name'] is None or json_data[first_dialog_id]['annotator_name'] == '':
            json_data = self.update_annotator_id_dialog(json_data)
        return json_data
            
    def annotator_id_empty(self, json_data):
        """checks if the annotator_name field in the json data is empty or not

        Args:
            json_data (string): the json data

        Returns:
            boolean: True if is empty, False if not.
        """
        first_dialog_id = next(iter(json_data))  # Get the first key in the JSON data
        if 'annotator_name' not in json_data[first_dialog_id] or json_data[first_dialog_id]['annotator_name'] is None:
            return True
        return False
    
    def update_annotator_id_dialog(self,json_data):
        """the dialog that is used to ask the annotator to give their name

        Args:
            json_data (string): gets the json data, to check if there is already a name and if there is, present it as the entry placeholder

        Returns:
            string: the json data after being updated with an annotator name
        """
        first_dialog_id = next(iter(json_data))  # Get the first key in the JSON data
        current_id = json_data[first_dialog_id].get('annotator_name')  # Get current annotator_id

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
            json_data = self.update_annotator_id(json_data)
            return json_data
        
        else:
            json_data = self.update_annotator_id_dialog(json_data)
            return json_data

             
    def update_annotator_id(self, json_data):
        """go through all the dialogs in the batch, and changes their annotator_name field to the annotator's name that was given through the dialog

        Args:
            json_data (string): the json data to with the field annotator name to be changed

        Returns:
            string: the json data after the field annotator_name has been changed
        """
        for dialog_id in json_data:
            json_data[dialog_id]['annotator_name'] = self.annotator_id

        self.annotator_id = self.annotator_id
        return json_data
    
class MongoData():
    def __init__(self, root, connection_string):
        self.client = MongoClient(connection_string)
        self.username = None
        self.usercode = None
        self.batch_id_list_index = None
        self.temp_batch_id_list_index = None
        self.count_batches = None
        self.root = root
        self.sign_in()
        self.finished = False
        self.json_data = self.load_json()
          
    def sign_in(self):
            """asks the user for a special code to be identified by the MongoDB database, so he will send back their current json_file in progress

            Raises:
                Exception: Raises when the user current working batch num not found in the database
            """
            usercode = simpledialog.askstring("Input", "Please sign in using your code", parent=self.root)
            if usercode is None: 
                self.root.destroy()
                return
            db = self.client.require_rewrite
            collection = db.annotators
            query = {"usercode": usercode}
            result = collection.find_one(query)
            if result != None:
                self.username = result['username']
                self.usercode = usercode
                self.count_batches = len(result['batches_order'])
                try:
                    self.batch_id_list_index = result['batches_order'][result['batch_id_list_index']]
                except:
                    raise Exception(f"The user batch is {result['batch_id_list_index']}, and it is not in the DB")
                return
            else:
                messagebox.showerror("Error", "username doesn't exist, please try again. (if you dont know your username ask Ori)")
                self.sign_in()

    def get_batch_num(self):
        """a get method for getting the current user batch_num

        Returns:
            int: the current batch num
        """
        if self.temp_batch_id_list_index != None:
            return self.temp_batch_id_list_index
        return self.batch_id_list_index
        
        
    def increase_annotator_batch_id_list_index(self):
        """called when a user finishes working on a batch, and asks mongoDB to increas the user's current batch num by one.

        Returns:
            dict: the response of the mongoDB
        """
        db = self.client.require_rewrite
        collection = db.annotators
        query = {"usercode": self.usercode}
        update = {"$inc": {"batch_id_list_index": 1}}  # Increment batch_id_list_index by 1
        result = collection.update_one(query, update)
        self.batch_id_list_index += 1
        return result
    
    def check_next_batch_exist(self):
        """check if theres a Batch with the num of (current_user_batch_num + 1)

        Returns:
            boolean: False if there isn't, True if there is.
        """
        
        if self.batch_id_list_index + 1 > self.count_batches:
            print("No more batches available.")
            return False
        
        return True
    
    
    def check_prev_batch_exist(self):
        """checks if theres a Batch with the num of (current_user_batch_num - 1), when user tries to go to his previous batches

        Returns:
            boolean: False if there isn't, True if there is.
        """
        
        if self.batch_id_list_index - 1 < 1:
            print("No prev batches available.")
            return False
        
        return True
    


    def next_batch(self):
        """sets the propety of the self.json_data, to the next batch

        Returns:
            boolean: True if operation was succseful, False if it wasn't
        """
        if not self.check_next_batch_exist():
            return False
        
        result = self.increase_annotator_batch_id_list_index()

        if result.matched_count > 0:
            print(f"User {self.username}'s batch_id_list_index increased by 1.")
        else:
            print("Username doesn't exist.")
            return False  # Stop the function if username doesn't exist

        self.json_data = self.load_json()  # Assuming this method loads the next batch of JSON data
        return True
    
    def prev_batch(self):
        """sets the propety of the self.json_data, to the previous batch

        Returns:
            boolean: True if operation was succseful, False if it wasn't
        """
        if not self.check_prev_batch_exist():
            return False
        
        if (self.temp_batch_id_list_index == None):
            self.temp_batch_id_list_index = self.batch_id_list_index - 1
        elif self.temp_batch_id_list_index > 1:
            self.temp_batch_id_list_index -= 1
        else:
            return False

        self.json_data = self.load_json(temp=True)  # Assuming this method loads the next batch of JSON data
        return True

    def load_json(self, test=False, temp=False):
        """asks the mongoDB for the json_file the user is working on

        Args:
            test (bool, optional): Is true when the function is called inside the test_if_annotation_updated_in_mongo. Defaults to False.
            temp (bool, optional): When a user goes back, a temporary batch_num is set for the navigation to not overide his progress. Defaults to False.

        Returns:
            string: the json file as string
        """
        if self.finished == True:
            return self.json_data
        data = None
        db = self.client.require_rewrite
        collection = db.json_annotations
        query = ''
        if temp == True:
            query = { "batch_id": self.temp_batch_id_list_index, "username": self.username, "usercode": self.usercode}
        else:
            query = { "batch_id": self.batch_id_list_index, "username": self.username, "usercode": self.usercode}
            
        result = collection.find_one(query)
        if result != None:
                if test == False and temp == False:
                    print('Annotator Already Started File, Going to First Empty Turn')
                data = result['json_string']
        else:
            query = {'batch_id': self.batch_id_list_index}
            collection = db.json_batches
            result = collection.find_one(query)
            if result == None:
                print('No more batches to annotate')
                self.finished == True
                return 'done'
            else:
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
        """opens a thread for and sends the user progress to the mongoDB
        """
        if self.finished == False:
            # Wrap the save_json logic in a method that can be run in a thread
            thread = threading.Thread(target=self.save)
            thread.start()
            # Optionally, you can join the thread if you need to wait for it to finish
            # thread.join()
            
    def save(self):
        """sends the json_file (that is saved in the program memory as string) back to mongoDB to be saved
        """
        db = self.client.require_rewrite
        collection = db.json_annotations
        query = {'usercode': self.usercode, 'batch_id': self.get_batch_num()}
        my_values = {"$set": {'username': self.username, 'usercode': self.usercode, 'batch_id': self.get_batch_num(), 'json_string': self.json_data}}
        update_result = collection.update_one(query, my_values, upsert=True)
        if update_result.matched_count > 0:
            print(f"Document with annotator_id: {self.username} and batch_id: {self.get_batch_num()} updated.")
        elif update_result.upserted_id is not None:
            print(f"New document inserted with id {update_result.upserted_id}.")
        else:
            print("No changes made to the database.")

    def test_if_annotation_updated_in_mongo(self):
        """opens a thread for a function that checks if the annotation the user did was saved inside mongoDB
        """
        thread = threading.Thread(target=self.test_if_annotation_updated_in_mongo_thread)
        thread.start()
    
    def test_if_annotation_updated_in_mongo_thread(self):
        temp_data = self.load_json(test=True)

        db = self.client.require_rewrite
        collection = db.json_annotations

        query = { "batch_id": self.batch_id_list_index, "username": self.username, "usercode": self.usercode}
        result = collection.find_one(query)

        if result != None:
            temp_data = result['json_string']
            if temp_data == self.json_data:
                return True
            else:
                return False
            
        return None

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
        """seaches for a file names target.json and reads in context, then saves it to the property of self.json_data"""
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
        """export the progress the annotator has made back inside the target.json
        """
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
        self.online = True
                                          
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
        self.current_dialog_num = 0
        self.current_turn_num = 0

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
        """ goes through the json_file and finds the next turn which is not filled already, then sets the program to show the turn"""
        for dialog_index, dialog_id in enumerate(self.data.json_data):
            annotations = self.data.json_data[dialog_id]['annotations']
            for turn_id in range(len(annotations)):
                turn_data = annotations[turn_id]['requires rewrite']
                if (turn_data == None):
                    self.current_dialog_num = dialog_index
                    self.current_turn_num = turn_id
                    return
                
        self.current_dialog_num = self.count_dialogs_in_batch()-1
        self.current_turn_num = self.count_turns_in_dialog()-1
    
    def are_all_fields_filled(self):
        """check if the turn the annotator is currently on is saved comletly, used before moving to the next turn

        Returns:
            boolean: True if everything is filled, False if not.
        """
        missing_fields = []

        # Check if annotator_id is filled
        first_dialog_id = next(iter(self.data.json_data))  
        if not self.data.json_data[first_dialog_id].get('annotator_name'):
            missing_fields.append("annotator name")

        # Check if annotator rewrite is filled
        dialog_id = self.get_dialog_id()
        turn_id = self.current_turn_num
        
        if self.require_rewrite.is_empty():
            missing_fields.append("Requires Rewrite")
                  

        if missing_fields and self.fields_check:
            tk.messagebox.showwarning("Warning", "The following fields are missing: " + ", ".join(missing_fields) + ". Please fill them in before proceeding.")
            return False
        
        return True
    
    def update_json(self):
        """updates the json_file inside the Data class (MongoDB or JsonHandler), to be saved later

        Raises:
            MemoryError: Raises when using online mode, and the annotation was not saved correctly in MongoDB

        Returns:
            boolean: Return True if opertion was successful, False if not
        """
        self.data.json_data = self.require_rewrite.update_json_data(self.get_dialog_id(), self.current_turn_num, self.data.json_data)
            
        # Save current state and move to next if all fields are filled
        self.data.save_json()

        if self.online == True:
            if self.data.test_if_annotation_updated_in_mongo() == False:
                raise MemoryError("Online data doesn't match local data, please contact Ori")
            
        return True
        
    def get_dialog_id(self):
        """simply gets the string of the dialog_id using the current num of the dialog in the batch file

        Returns:
            string: the dialog_id
        """
        return list(self.data.json_data.keys())[self.current_dialog_num]


    
    def init_turn(self):
        """This is an important function which initilaises and update the GUI each turn
        """
        self.progress.update_current_turn_dialog_labels(self.current_dialog_num, self.current_turn_num, self.data.json_data, len(self.data.json_data[self.get_dialog_id()]['annotations']))
        self.dialog_frame.display_dialog(self.get_dialog_id(), self.current_turn_num, self.data.json_data)
        self.require_rewrite.update_entry_text(self.get_dialog_id(), self.current_turn_num, self.data.json_data)  
        self.font.update_font_size_wrapper()
        self.create_focus_list()  
        progress_string = f"Turn={self.current_turn_num+1} | Dialog={self.current_dialog_num+1}"
        if self.online == True: progress_string += f" | Batch={self.data.get_batch_num()}"
        print(progress_string)             

    def count_turns_in_dialog(self):
        """count the number of turn in the dialog

        Returns:
            int: number of turns in dialog
        """
        return len(self.data.json_data[self.get_dialog_id()]['annotations'])
    
    def count_dialogs_in_batch(self):
        """count the number of dialogs in the batch file

        Returns:
            int: number of dialogs in batch
        """
        return len(self.data.json_data)
     
    def prev_turn(self):
        """goes to the previous turn in the dialog
            if there are no more turns, go to the prev dialog,
            if there are no more dialogs and using mongo, goes to prev batch (if offline need to manually change target.json)

        Returns:
            boolean: Return True if opertion was successful, False if not
        """
        if self.current_turn_num > 0:
            self.current_turn_num -= 1
            
        elif self.current_dialog_num > 0:
            self.current_dialog_num -= 1
            self.current_turn_num = self.count_turns_in_dialog() - 1
            
        elif self.online == True:
            if not self.prev_batch():
                return False
            
        self.init_turn()
        
        return True
    
    def next_turn(self):
        """goes to the previous turn in the dialog
            if there are no more turns, go to the next dialog,
            if there are no more dialogs and using mongo, goes to next batch (if offline need to manually change target.json)

        Returns:
            boolean: Return True if opertion was successful, False if not
        """
        if not self.are_all_fields_filled():
            return False
        
        elif not self.update_json():
            return False
        
        if self.current_turn_num < self.count_turns_in_dialog() - 1:
            self.current_turn_num += 1
            
        elif self.current_dialog_num < self.count_dialogs_in_batch() - 1:
            self.current_dialog_num += 1
            self.current_turn_num = 0
            
        elif self.online == True:
            if not self.next_batch():
                tk.messagebox.showinfo(title='Finished Annotating!', message='No More Annotations', icon='info')
                return False
            
            else:
                self.data.json_data = self.annotator_id.update_annotator_id(self.data.json_data) #update annotator name
                self.current_dialog_num = 0
                self.current_turn_num = 0
              
        self.init_turn()
        
        return True

    def prev_dialog(self):
        """used in the prev dialog button to go to prev dialog
        """
       
        if self.current_dialog_num > 0:
                if not self.require_rewrite.is_empty():
                        self.update_json()
                self.current_dialog_num -= 1
                self.current_turn_num = self.count_turns_in_dialog()-1
                self.init_turn()
                self.font.update_font_size_wrapper()
        elif (self.online == True and self.data.check_prev_batch_exist()):
                if not self.require_rewrite.is_empty():
                            self.update_json()
                self.data.prev_batch()
                self.current_dialog_num = self.count_dialogs_in_batch()-1
                self.current_turn_num = self.count_turns_in_dialog()-1
                self.init_turn()
        else:
            tk.messagebox.showwarning("Warning", "This is the first dialog")

    def next_dialog(self):
        """used in the next dialog button to go to prev dialog
        """
       
        if self.current_dialog_num < len(self.data.json_data) - 1:
            if self.fields_check:
                if self.are_all_turns_filled(self.current_dialog_num):
                    if not self.require_rewrite.is_empty():
                        self.update_json()
                    self.current_dialog_num += 1
                    self.current_turn_num = 0
                    self.init_turn()
                    
                else:
                    tk.messagebox.showwarning("Warning", "Not all turns in this dialog are filled")
            else:
                self.update_json()
                self.current_dialog_num += 1
                self.current_turn_num = 0
                self.init_turn()
                

        elif (self.online == True and self.data.check_next_batch_exist()):
            if self.fields_check:
                if self.are_all_turns_filled(self.current_dialog_num):
                    if not self.require_rewrite.is_empty():
                        self.update_json()
                    self.data.next_batch()
                    self.current_dialog_num = 0
                    self.current_turn_num = 0
                    self.init_turn()
                    
    def next_batch(self):
        """in online mode, goes to the next batch

        Returns:
            boolean: Return True if opertion was successful, False if not
        """
        if self.online == False and not self.data.check_next_batch_exist():
            return    
        if not self.data.next_batch():
            return
        self.data.json_data = self.annotator_id.update_annotator_id(self.data.json_data)
        self.current_dialog_num = 0
        self.current_turn_num = 0
        return True
    
    def prev_batch(self):
        """in online mode, goes to the prev batch

        Returns:
            boolean: Return True if opertion was successful, False if not
        """
        if self.online == False and not self.data.check_prev_batch_exist():
            return False
        if not self.data.prev_batch():
            return False
        self.current_dialog_num = self.count_dialogs_in_batch() - 1
        self.current_turn_num = self.count_turns_in_dialog() - 1
        return True
                                    
    def are_all_turns_filled(self):
        """when going to the next dialog using the button, checks if all the turns in the dialog are filled


        Returns:
            boolean: Return True if opertion was successful, False if not
        """
        dialog_data = self.data.json_data[self.get_dialog_id()]
        for turn in dialog_data['annotations']:
            if turn['requires rewrite'] == None: return False
        return True

    def create_focus_list(self):
            """used for the comfort of the annotator, to go to the next field in the GUI when pressing enter
            creates to order of elements focus on
            """
            self.focus_list = []
            self.focus_index = 0
            self.first_focus_action = True
            self.focus_list.append(self.require_rewrite.requires_rewrite_entry)
            
            self.focus_list.append(self.save_button)
    
    def next_focus(self, event=None):
        """used for the comfort of the annotator, to go to the next field in the GUI when pressing enter
        goes to the next element in the focus list
        """
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
        """used for the comfort of the annotator, to go to the next field in the GUI when pressing enter
        goes to the prev element in the focus list
        """
        if self.first_focus_action:
            self.focus_index = len(self.focus_list)  # Start from the end
            self.first_focus_action = False

        self.focus_index -= 1
        if self.focus_index < 0:
            self.focus_index = len(self.focus_list) - 1

        self.focus_list[self.focus_index].focus()

def main():
    online = True
    if online == False:
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
    try:
        main()
    except Exception:
        with open("error_log.txt", "w") as f:
            traceback.print_exc(file=f)