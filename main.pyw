import time
from tkinter import Tk
import defs
import pyaimp
from  tkinter import *
from tkinter.ttk import *
import os
import shutil
import threading
def like_():
    global y, a
    id = y.get_current_id(a)
    y.like(id)
def dislike_():
    global y, a
    id = y.get_current_id(a)
    y.dislike(id, a)
def refresh_radio():
    global y, a
    y.progress_type = "Setting up stuff"
    folder = "./Y/radio"
    
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
    global y, a
    a.add_dirs_to_playlist(rf"{os.getcwd()}\Y\daily")
    a.next()
def update_label():
    while True:
        
        global y, a, label, progress
        while y.progress_type != None:
            time.sleep(1)
            label['text'] = y.progress_type
            if y.progress_type == "Fetching tracks":
                progress['mode'] = 'determinate'
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
if __name__ == "__main__":
    y = defs.YM()
    a = pyaimp.Client()
    a.set_shuffled(True)
    master = Tk()
    master.geometry("300x380")
    master.title("Aimp Supplement")
    
    btn1 = Button(master, text = "Лайк", command = like_)
    btn2 = Button(master, text = "Убрать навсегда", command = dislike_)
    btn3 = Button(master, text = "Обновить радио", command = refresh_radio)
    btn4 = Button(master, text = "Радио", command = radio)
    btn45 = Button(master, text = "Дэйли", command = daily)
    btn5 = Button(master, text = "Любимое", command = likes)
    label=Label(master, text="Currently idling", font=('Aerial 18'))
    progress = Progressbar(master, orient=HORIZONTAL, length=100)
    label.pack(pady = 10)
    progress.pack(pady = 10)
    btn1.pack(pady = 10)
    btn2.pack(pady = 10)
    btn3.pack(pady = 10)
    btn4.pack(pady = 10)
    btn45.pack(pady = 10)
    btn5.pack(pady = 10)
    t = threading.Thread(name='child procs', target=update_label)
    t.start()
    
    
    
    mainloop()