import tkinter as tk
from tkinter import Toplevel, ttk, filedialog
from tkinter import messagebox
from tkinter import filedialog

import random
import sys
import os
import csv
from datetime import datetime

import numpy as np
import pandas as pd
from pandastable import Table
from matplotlib import pyplot as plt

import sounddevice as sd

# import my library
sys.path.append('.\\lib') # Point to custom library file
import tmsignals as ts # Custom library
import importlib 
importlib.reload(ts) # Reload custom module on every run

# Define startup values
speakers = np.arange(1,9)

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Check for existing etc folder
if os.path.isdir(_thisDir + os.sep + 'etc' + os.sep):
    print("Found etc folder.")
else:
    print("No etc folder found; creating one.")
    os.mkdir(_thisDir + os.sep + 'etc' + os.sep)
    isdir = os.path.isdir(_thisDir + os.sep + 'etc' + os.sep)
    if isdir:
        print("etc folder created successfully.")
    else:
        print("Problem creating etc folder.")


class Speaker:
    """ Speaker object with position number, offset, and 
    calibrated(boolean) attributes.
    """
    def __init__(self, position, offset=None):
        self.position = position
        self.offset = offset
        self.calibrated = False


# Instantiate speaker objects and store in list  
speaker_list = []
for speaker in speakers:
    spkr = Speaker(speaker)
    speaker_list.append(spkr)


def device_check():
    """ Check if an audio device has been selected.
    """
    global sndDevice
    try:
        sndDevice = pd.read_csv('.\\etc\\Sound_Device.csv')
        sndDevice = int(sndDevice.columns[0])
        sd.default.device = sndDevice
    except:
        messagebox.showerror(title="No sound device selected!", message="Please select a sound device before continuing!")
        tools_list_audio_devs()


def mk_wgn():
    """ Function to generate white Gaussian noise.
    """
    fs = 48000
    dur=3
    syslevel = float(ent_sysvolume.get())
    # Set random seed
    # This ensures the same random values are used to 
    # generate the noise every time
    random.seed(4)
    wgn = [random.gauss(0.0, 1.0) for i in range(fs*dur)]
    wgn = ts.doNormalize(wgn)
    wgn = ts.setRMS(wgn,syslevel)
    wgn = wgn - np.mean(wgn) # Remove DC offset
    return wgn


def play_snd():
    # check for default audio device
    device_check()

    syslevel = float(ent_sysvolume.get())
    # Create white Gaussian noise
    wgn = mk_wgn()
    fs = 48000
    dur = len(wgn) / fs

    if syslevel > -10:
        resp = messagebox.askyesnocancel(title="Danger!", 
            message=("System volume should NEVER be above -10!\n\n" +
                "Do you have a FANTASTIC reason for continuing at " +
                "this level?"))
        if resp:
            pass
        if not resp: 
            return

    chan = int(selected_speaker.get())
    sd.play(wgn, fs, mapping=chan)
    sd.wait(dur)

root = tk.Tk()
root.title("Balance Speakers")
root.withdraw()

options_sysvolume = {'padx':10, 'pady':10}
options_speakers = {'padx':10, 'pady':10}
options_next = {'padx':10, 'pady':10}

# Frames for root menu organization
frm_sysvolume = ttk.Frame(root)
frm_sysvolume.grid(column=0, row=0, **options_sysvolume)

sep_slm = ttk.Separator(root, orient="vertical")
sep_slm.grid(column=1, row=0, rowspan=1, sticky='ns')

frm_slm = ttk.Frame(root)
frm_slm.grid(column=2, row=0, rowspan=2, **options_sysvolume)

#sep_speakers = ttk.Separator(root, orient="horizontal", width=3)
#sep_speakers.grid(column=0, columnspan=4, row=1, sticky='ew')
frm_sep_speakers = tk.Frame(root, width=10)
frm_sep_speakers.grid(column=0, columnspan=4, row=1, sticky="ew")
frm_sep_speakers["background"] = "gray"

frm_speakers = ttk.LabelFrame(root, text="Speaker Number")
frm_speakers.grid(column=0, columnspan=2, row=2, **options_speakers)

frm_next_button = ttk.Frame(root)
frm_next_button.grid(column=2, row=2, sticky='w', **options_next)

options_sys_widgets = {'pady':(0,10)}

# Widgets for system volume
lbl_sysvolume = ttk.Label(frm_sysvolume, text="System Volume: ")
lbl_sysvolume.grid(column=0, row=0, sticky='e', **options_sys_widgets)
syslevel = tk.IntVar(value=-50)
ent_sysvolume = ttk.Entry(frm_sysvolume, textvariable=syslevel, width=5)
ent_sysvolume.grid(column=1, row=0, sticky='w', **options_sys_widgets)
lbl_play = ttk.Label(frm_sysvolume, text="Calibration Stimulus: ")
lbl_play.grid(column=0, row=1, sticky='e')
btn_play = ttk.Button(frm_sysvolume, text="Play", command=play_snd)
btn_play.grid(column=1, row=1, sticky='w')

# Widgets for slm reading
lbl_slm = ttk.Label(frm_slm, text="SLM Reading: ")
lbl_slm.grid(column=0, row=0)
ent_slm = ttk.Entry(frm_slm, width=5)
ent_slm.grid(column=1, row=0)

# Widgets for speakers
selected_speaker = tk.StringVar()
for idx, speaker in enumerate(speakers):
    lbl_speaker_num = ttk.Label(frm_speakers,text=speaker)
    lbl_speaker_num.grid(column=idx,row=0,padx=(0,5))
    rad_speaker_num = ttk.Radiobutton(frm_speakers,text='',takefocus=0,value=speaker,variable=selected_speaker)
    rad_speaker_num.grid(column=idx,row=1)
    if speaker == 1:
        selected_speaker.set(1)


class Updater:
    def __init__(self, selected_speaker, slm_val):
        self.Speaker = speaker_list[selected_speaker-1]
        self.slm_val = slm_val

    def update_speaker(self):
        # ref_level is taken from the SLM reading of SPEAKER 1
        try:
            speaker_offset = ref_level - self.slm_val
        except:
            messagebox.showerror(
                title="Missing Reference",
                message="You must start with Speaker 1!"
            )
            return
        self.Speaker.offset = speaker_offset
        self.Speaker.calibrated = True
        #print(f"Speaker {str(self.Speaker.position)} calibrated: {str(self.Speaker.calibrated)}\n")
        #print(f"Speaker {str(self.Speaker.position)} offset: {str(self.Speaker.offset)}\n")
        #for speaker in speaker_list:
        #    print(speaker.calibrated)
        #print("\n")


def go_to_next():
    """ Multi-purpose function: 
        1. get the selected speaker
        2. set the reference level to speaker 1
        3. select the next speaker
        4. clear the SLM reading entry box value
     """
    global ref_level
    # Get currently selected speaker
    the_speaker = int(selected_speaker.get())
    #print(f'"The current speaker is: {str(the_speaker)}')

    # Try to read the SLM value
    try:
        slm_val = int(ent_slm.get())
    except:
        messagebox.showerror(title="Invalid Level!",
        message="Please enter a valid sound level!")
        return

    # The SLM reading from SPEAKER 1 is used as reference
    if the_speaker == 1:
        ref_level = slm_val

    # Set next speaker 
    if the_speaker >= len(speaker_list):
        next_speaker = 1
    else:
        next_speaker = the_speaker + 1
    selected_speaker.set(next_speaker)

    # Run the updater to store cal values in speaker
    the_updater = Updater(the_speaker, slm_val)
    the_updater.update_speaker()

    # Clear SLM reading entry box text
    ent_slm.delete(0, 'end')


# Splice button
btn_Next = ttk.Button(frm_next_button, text="Submit", command=go_to_next)
btn_Next.grid(column=len(speakers)+1, row=1, **options_sysvolume)


########################
#### MENU FUNCTIONS ####
########################
def tools_verify_levels():
    """ Multi-purpose function:
    1. Loads offset file
    2. Checks audio device
    3. Creates noise
    4. Applies offsets
    5. Presents noise one speaker at a time
    """
    # This should be its own function: loads offset file
    # and stores in dict
    filename = filedialog.askopenfilename(initialdir=_thisDir)
    df = pd.read_csv(filename,
    header=None, index_col=0)
    offset_dict = df.to_dict()
    offset_dict = offset_dict[1] # to_dict returns a list, so grab first one

    # Check whether audio device has been set. 
    # Use stored value if possible. 
    device_check()
    print(f"Setting default sound device to: {sndDevice}")

    # Get the system (overall) level from the GUI
    syslevel = float(ent_sysvolume.get())

    # Create white Gaussian noise
    fs = 48000
    dur = 10
    random.seed(4)
    wgn = [random.gauss(0.0, 1.0) for i in range(fs*dur)]
    wgn = ts.doNormalize(wgn)
    wgn = ts.setRMS(wgn,syslevel)
    wgn = wgn - np.mean(wgn) # Remove DC offset

    # Find RMS of noise in dB
    wgn_rms_db = ts.mag2db(ts.rms(wgn))
    print(f"RMS in dB of wgn: {wgn_rms_db}")

    # Apply offsets to noise and present, 
    # one speaker at a time
    #wgn_lists = []
    for key in offset_dict:
        selected_speaker.set(int(key)) # is the screen not updating during/between playback?
        print(f"Speaker {key} offset: {offset_dict[key]}")
        wgn = ts.setRMS(wgn, (float(wgn_rms_db) - float(offset_dict[key])))
        print(f"RMS in dB of wgn with offset: {ts.mag2db(ts.rms(wgn))}")
        #wgn_lists.append(wgn)
        sd.play(wgn.T, fs, mapping=int(key))
        sd.wait(dur)
    #wgn_matrix = np.array(wgn_lists)


def file_write_offsets():
    """ Write offsets to file.
    """
    for speaker in speaker_list:
        if not speaker.calibrated:
            resp = messagebox.askyesno(
                title="Uncalibrated Speakers!",
                message=(f"Speaker {str(speaker.position)} has not been balanced, " +
                "are you sure you want to continue??")
            )
            if not resp:
                return

    now = datetime.now()
    date_stamp = now.strftime("%Y_%b_%d_%H%M")
    with open('.\\speaker_offsets_' + str(date_stamp) + '.csv', 'w', newline='') as f:
        for speaker in speaker_list:
            writer = csv.writer(f)
            writer.writerow([str(speaker.position), str(speaker.offset)])

    messagebox.showinfo(title="Success!", 
        message="Offset file successfully created!")


def tools_list_audio_devs():
    """ Return a table with the available audio devices.
    """
    global sndDevice
    audDev_win = Toplevel(root)
    audDev_win.title('Audio Device List')
    audDev_win.withdraw()
    #audDev_win.wm_iconbitmap(img)

    def doDevID():
        global sndDevice
        try:
            sndDevice = int(entDeviceID.get())
            sd.default.device = sndDevice
            # make a text file to save data
            dataFile = _thisDir + os.sep + 'etc' + os.sep + 'Sound_Device.csv'
            with open(dataFile, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([str(sndDevice)])

            audDev_win.destroy()
        except:
            messagebox.showwarning(title='Oops!', message="Not a valid selection!\nPlease select another device!")

    options = {'padx':10, 'pady':10}
    options_small = {'padx':5, 'pady':5}
    frmID = ttk.Frame(audDev_win)
    frmID.grid(column=0, row=0, **options)

    frmTable = ttk.Frame(audDev_win)
    frmTable.grid(column=0, row=1, **options)

    lblInstr = ttk.Label(frmID, text="Enter the audio device ID:")
    lblInstr.grid(column=0, row=0, sticky='e', **options_small)
   
    entDeviceID = ttk.Entry(frmID)
    entDeviceID.grid(column=1, row=0, sticky='w', ** options_small)
    entDeviceID.focus()

    btnDeviceID = ttk.Button(frmID, text="Submit", command=doDevID)
    btnDeviceID.grid(column=0, row=1, sticky='w', **options_small)

    deviceList = sd.query_devices()
    names = [deviceList[x]['name'] for x in np.arange(0,len(deviceList))]
    chans_in =  [deviceList[x]['max_output_channels'] for x in np.arange(0,len(deviceList))]
    ids = np.arange(0,len(deviceList))
    df = pd.DataFrame({"device_id": ids, "name": names,"chans_in": chans_in})

    pt = Table(frmTable,dataframe=df, showtoolbar=True, showstatusbar=True)
    table = pt = Table(frmTable, dataframe=df)
    table.grid(column=0, row=0)
    pt.show()

    # Center root based on new size
    audDev_win.update_idletasks()
    window_width = audDev_win.winfo_width()
    window_height = audDev_win.winfo_height()
    # get the screen dimension
    screen_width = audDev_win.winfo_screenwidth()
    screen_height = audDev_win.winfo_screenheight()
    # find the center point
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    # set the position of the window to the center of the screen
    audDev_win.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    audDev_win.resizable(False, False)
    audDev_win.deiconify()

    audDev_win.mainloop()


# Menu
def confirm_exit():
    answer = messagebox.askyesno(title='Really?',
        message='Are you sure you want to quit?')
    if answer:
        root.destroy()

# create a menubar
menubar = tk.Menu(root)
root.config(menu=menubar)
# create the File menu
file_menu = tk.Menu(menubar, tearoff=False)
# add menu items to the File menu
file_menu.add_command(
    label='Make Offset File',
    command=file_write_offsets
)
file_menu.add_separator()
file_menu.add_command(
    label='Exit',
    command=confirm_exit
)
# add the File menu to the menubar
menubar.add_cascade(
    label="File",
    menu=file_menu
)
# Create Tools menu
tools_menu = tk.Menu(
    menubar,
    tearoff=0
)
# Add items to the Tools menu
tools_menu.add_command(
    label='Audio Devices',
    command=tools_list_audio_devs)
tools_menu.add_command(
    label='Calibration Test',
    command=tools_verify_levels)
# Add Tools menu to the menubar
menubar.add_cascade(
    label="Tools",
    menu=tools_menu
)
# create the help menu
help_menu = tk.Menu(
    menubar,
    tearoff=0
)
# add items to the Help menu
# help_menu.add_command(
#     label='Help',
#     command=lambda: messagebox.showinfo(title="Help", message="Not yet available!"))
help_menu.add_command(
    label='About',
    command=lambda: messagebox.showinfo(title="About Balance Speakers",
    message="Version: 1.0.0\nWritten by: Travis M. Moore\nCreated: 06/09/2022\nLast Updated: 06/10/2022")
)
# add the Help menu to the menubar
menubar.add_cascade(
    label="Help",
    menu=help_menu
)

# Center root based on new size
root.update_idletasks()
#root.attributes('-topmost',1)
window_width = root.winfo_width()
window_height = root.winfo_height()
# get the screen dimension
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
# find the center point
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)
# set the position of the window to the center of the screen
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
root.resizable(False, False)
root.deiconify()

root.mainloop()
