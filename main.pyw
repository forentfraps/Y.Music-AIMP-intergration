import time
from tkinter import Tk
import defs
import pyaimp
from  tkinter import *
from tkinter.ttk import *
import os
import shutil
import threading
import ctypes
from multiprocessing import Process
import sys

def get_cur_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) + f'{os.sep}Y{os.sep}'

    elif __file__:
        return os.path.dirname(__file__) + f'{os.sep}Y{os.sep}'
    return False
def like_():
    global y, a
    id = y.get_current_id(a)
    y.like(id)
def dislike_():
    global y, a
    id = y.get_current_id(a)
    y.dislike(id, a)
def refresh_radio():
    global y, a, PATH
    y.progress_type = "Setting up stuff"
    folder = f"{PATH}radio"
    
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    y.thr_bulk_radio()
def daily():
    global a
    a.add_dirs_to_playlist(f"{PATH}daily")
    a.next()
def update_label():
    while True:
        global label, progress, y , a
        while y.progress_type != None:
            time.sleep(1)
            label['text'] = y.progress_type
            if y.progress_type == "Fetching tracks":
                progress['mode'] = 'determinate'
                progress.stop()
                progress['value'] = y.progress
            else:
                if progress['mode'] != 'indeterminate':
                    progress.start(10)
                    progress['mode'] = 'indeterminate'
        progress['mode'] = 'determinate'
        progress.stop()
        progress['value'] = 0
        label['text'] = "Currently idling"
        time.sleep(1)
def likes():
    global y, a
    a.add_dirs_to_playlist(rf"{os.getcwd()}\Y\likes")
    a.next()
def radio():
    global y, a
    a.add_dirs_to_playlist(rf"{os.getcwd()}\Y\radio")
    a.next()
    
def discord_status(d):
    while True:
        d.discord_update_DEV()
        time.sleep(1)
if __name__ == "__main__":
    PATH = get_cur_path()
    myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    y = defs.YM()
    a = pyaimp.Client()
    d = None
    try:
        d = defs.Discord(y = y, a = a, token = None) 
    except Exception as e:
        print(f"{e}, in main, while initializing discord class")
    a.set_shuffled(True)
    master = Tk()
    master.geometry("245x280")
    master.title("Aimp Supplement")
    master.iconbitmap(default='logo.ico')
    
    radio_but=Button(master)
    radio_but["text"] = "Radio"
    radio_but.place(x=10,y=10,width=100,height=40)
    radio_but["command"] = radio
    
    daily_but=Button(master)
    daily_but["text"] = "Daily"
    daily_but.place(x=10,y=70,width=100,height=40)
    daily_but["command"] = daily
    
    likes_but=Button(master)
    likes_but["text"] = "Likes"
    likes_but.place(x=10,y=130,width=100,height=40)
    likes_but["command"] = likes
    
    like_but=Button(master)
    like_but["text"] = "Like"
    like_but.place(x=10,y=240,width=100,height=30)
    like_but["command"] = like_
    
    dislike_but = Button(master)
    dislike_but["text"] = "Dislike"
    dislike_but.place(x=135,y=240,width=100,height=30)
    dislike_but["command"] = dislike_
    
    refradio_but = Button(master)
    refradio_but["text"] = "Refresh Radio"
    refradio_but.place(x=135,y=10,width=100,height=40)
    refradio_but["command"] = refresh_radio
    
    label=Label(master, font=11)
    label["text"] = "Setting up stuff..."
    label.place(x=135,y=115,width=120,height=40)
    
    progress=Progressbar(master, orient=HORIZONTAL, length=100)
    progress["value"] = 0
    progress.place(x=135,y=70,width=100,height=40)
    if d:
        threading.Thread(name = 'discord status', target = discord_status, args = (d, ), daemon=True).start()
        threading.Thread(name = 'discord bio', target = d.update_bio, daemon=True).start()
    threading.Thread(name='update label', target=update_label, daemon=True).start()
    
    
    
    mainloop()
