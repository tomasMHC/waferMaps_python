import os
import tkinter as tk
import tkinter.filedialog as fd
import re
import shutil
from tkinter import messagebox

# EPI reclaim: "wdddddddSSSd"
# onsemi: "SSSSddd-dd"
ID_STRUCTURE="SSSSddd-dd" # w - any character from a-Z or 1-9 or "_" ; d - digit, s - small letter, S - capital letter

def convert_to_regex(id_structure):
    # Initialize an empty regex pattern
    regex_pattern = ""
    
    # Dictionary to map structure characters to regex patterns
    mapping = {
        'd': r'\d',  # digit
        's': r'[a-z]',  # letter
        '-': r'-',  # hyphen
        "S": r"[A-Z]",
        "w": r"\w"
    }
    
    # Iterate over each character in the ID structure
    for char in id_structure:
        if char in mapping:
            regex_pattern += mapping[char]
        else:
            raise ValueError(f"Unsupported character '{char}' in ID structure")
    
    # Return the complete regex pattern
    return regex_pattern

def rege(zoznam):
        regex=[]
        for i in zoznam:
            x=re.findall(convert_to_regex(ID_STRUCTURE),i)
            x=str(x).replace("'","")
            x=x.replace("[","")
            x=x.replace("]","")
            regex.append(x)
        return regex

def regex_single(string):
    x=re.findall(convert_to_regex(ID_STRUCTURE),string)
    x=str(x).replace("'","")
    x=x.replace("[","")
    x=x.replace("]","")
    return x

def find_and_copy():
    
    root=tk.Tk()
    root.withdraw()
    vstupne=[]
    vstup=fd.askdirectory(parent=root, title="Choose directory that will be matched")
    print(f"Vstup folder: {vstup}")
    for file in os.listdir(vstup):
        if file.endswith(".mat"):
            vstupne.append((file))
    
    search_lasers=rege(vstupne)
    print(f"Vstupne: {len(vstupne)}\n {vstupne}")
    print(f"Search lasers: {len(search_lasers)}\n {search_lasers}")
    pokracovat=True
    while pokracovat==True:
        root=tk.Tk()
        root.withdraw()
        vystup=fd.askdirectory(parent=root, title="Choose a directory to pick files from")
        pred_pyth_path=os.path.join(vstup,"pred_pyth")
        isExist=os.path.exists(pred_pyth_path)
        files_in_vystup=os.listdir(vystup)
        # print(f"Files in vystup: {files_in_vystup}")
        if not isExist:
            os.makedirs(pred_pyth_path)   
        copied_number=0
        latest_time=0
        wafer_dict={}
        path_dict={}
        for file in files_in_vystup:
            laser=regex_single(file)
            if laser in search_lasers and (file.endswith(".mat") or file.endswith(".jpg")):

                file_path=os.path.join(vystup,file)
                creation_time= os.path.getctime(file_path)
                wafer_dict[laser]=creation_time
                path_dict[laser]=file_path

                if wafer_dict[laser] < creation_time:
                    wafer_dict[laser]=creation_time
                    path_dict[laser]=file_path
                    
        for i in path_dict.values():
            shutil.copy2(i, pred_pyth_path)
            print(f"{regex_single(file)} copied from: {os.path.join(vystup, file)} to: {pred_pyth_path}")
            copied_number=copied_number+1
        else:
            print(f"{regex_single(file)} Not copied")
        print(wafer_dict)
        root=tk.Tk()
        root.withdraw()
        answer = messagebox.askyesnocancel("Question", f"Copied {copied_number//2} files. Continue picking files?")
        if answer==False:
            pokracovat=False
find_and_copy()