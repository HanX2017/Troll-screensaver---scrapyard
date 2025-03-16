import cv2
import numpy as np
import tkinter as tk
import os
import random
import threading
import time
import ctypes
from pynput import keyboard, mouse
import pygetwindow as gw
from PIL import Image, ImageTk

user32 = ctypes.windll.user32

def hide_taskbar():
    user32.ShowWindow(user32.FindWindowW("Shell_TrayWnd", None), 0)  

def show_taskbar():
    user32.ShowWindow(user32.FindWindowW("Shell_TrayWnd", None), 1)  

hide_taskbar()

def force_window_focus(window_title):
    while True:
        try:
            win = gw.getWindowsWithTitle(window_title)
            if win:
                win[0].activate()
                win[0].maximize()
        except:
            pass
        time.sleep(0.5)


face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
detection_active = False
bsod_active = False
last_detection_time = time.time()
detection_timeout = 5 
time_to_unlock = 10

def exit_program():
    print("[INFO] EXIT。")
    show_taskbar()
    os._exit(0)

def on_press(key):
    global detection_active, last_detection_time
    if key == keyboard.Key.tab:
        exit_program()
    detection_active = True
    last_detection_time = time.time()
    print("[INFO] 鍵盤輸入偵測，觸發保護模式。")

def on_click(x, y, button, pressed):
    global detection_active, last_detection_time
    detection_active = True
    last_detection_time = time.time()
    print("[INFO] 滑鼠點擊偵測，觸發保護模式。")

keyboard_listener = keyboard.Listener(on_press=on_press)
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener.start()
mouse_listener.start()

def detect_face():
    global detection_active, last_detection_time
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))
        if len(faces) > 0:
            detection_active = True
            last_detection_time = time.time()
            print("[INFO] 人臉偵測，觸發保護模式。")
        time.sleep(1)
    cap.release()

def monitor():
    global detection_active
    while True:
        if detection_active and not bsod_active and time.time() - last_detection_time <= detection_timeout:
            hide_taskbar()
            event = random.choice([trigger_bsod, trigger_typing_challenge, trigger_math_challenge])
            print(f"[INFO] 隨機選擇 {event.__name__} 作為懲罰事件。")
            event()
            show_taskbar()
        time.sleep(1)

def create_fullscreen_window(root, title):
    root.attributes('-fullscreen', True)
    root.overrideredirect(True)
    root.title(title)
    threading.Thread(target=force_window_focus, args=(title,), daemon=True).start()

def trigger_bsod():
    global bsod_active
    bsod_active = True
    print("[INFO] 觸發 BSOD 螢幕。")
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    create_fullscreen_window(root, "BSOD_Screen")
    
    root.config(cursor="none")
    
    try:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        img = Image.open("BSOD.png")
        img = img.resize((screen_width, screen_height), Image.LANCZOS) 
        img_tk = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[ERROR] 無法載入 BSOD 圖片: {e}")
        root.after(100, root.destroy)
        return
    
    label = tk.Label(root, image=img_tk)
    label.image = img_tk 
    label.pack()
    
    def check_bsod_status():
        while True:
            if time.time() - last_detection_time > 5:
                print("[INFO] 5秒無偵測到人臉或輸入，解除BSOD。")
                root.after(100, root.destroy)
                show_taskbar()
                break
            time.sleep(1)
    
    threading.Thread(target=check_bsod_status, daemon=True).start()
    root.mainloop()
    bsod_active = False
    print("[INFO] 10秒正常使用時間。")
    time.sleep(time_to_unlock)


def trigger_typing_challenge():
    print("[INFO] 觸發文字輸入挑戰。")
    try:
        with open("strings.txt", "r", encoding="utf-8") as f:
            challenges = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("[ERROR] 沒有strings.txt。")
        return
    
    if not challenges:
        print("[ERROR] 沒有可用的文字挑戰。")
        return
    
    challenge_text = random.choice(challenges)
    root = tk.Tk()
    create_fullscreen_window(root, "Typing_Challenge")
    
    frame = tk.Frame(root)
    frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER) 
    
    tk.Label(frame, text="請輸入以下內容：", font=("Arial", 20)).pack()
    tk.Label(frame, text=challenge_text, font=("Arial", 40, "bold")).pack()
    entry = tk.Entry(frame, font=("Arial", 20), width=40)
    entry.pack()
    
    error_label = tk.Label(frame, text="", font=("Arial", 18), fg="red")
    error_label.pack()
    
    def check_input():
        if entry.get() == challenge_text:
            root.destroy()
            show_taskbar()
            print("[INFO] 文字輸入正確，解除保護模式。")
            time.sleep(time_to_unlock)
        else:
            error_label.config(text="輸入錯誤，請再試一次！")
    
    tk.Button(frame, text="送出", font=("Arial", 18), command=check_input).pack()
    root.mainloop()


def trigger_math_challenge():
    print("[INFO] 觸發數學挑戰。")
    question_files = [f for f in os.listdir("math_questions") if f.endswith(".png")]
    if not question_files:
        print("[ERROR] 無數學題目可用。")
        return
    
    selected_question = random.choice(question_files)
    question_id = selected_question.split(".")[0]
    
    with open("answers.txt", "r") as f:
        answers = dict(line.strip().split("=") for line in f)
    correct_answer = answers.get(question_id, "")
    
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.title("Math Challenge")
    
    frame = tk.Frame(root)
    frame.pack(expand=True)
    
    try:
        img = Image.open(f"math_questions/{selected_question}")
        img = img.resize((600, 400), Image.LANCZOS)  
        img_tk = ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[ERROR] 無法載入數學題圖片: {e}")
        root.destroy()
        return
    
    label = tk.Label(frame, image=img_tk)
    label.image = img_tk
    label.pack()
    
    entry = tk.Entry(frame, font=("Arial", 20))
    entry.pack()
    
    error_label = tk.Label(frame, text="", font=("Arial", 18), fg="red")
    error_label.pack()
    
    def check_answer():
        if entry.get() == correct_answer:
            root.destroy()
            show_taskbar()
            print("[INFO] 數學題答對，解除保護模式。")
            time.sleep(time_to_unlock)
        else:
            error_label.config(text="答案錯誤，請再試一次！")
    
    tk.Button(frame, text="送出", font=("Arial", 18), command=check_answer).pack()
    
    root.mainloop()

print("[INFO] 啟動人臉偵測與行為監控。")
face_thread = threading.Thread(target=detect_face, daemon=True)
face_thread.start()
monitor_thread = threading.Thread(target=monitor, daemon=True)
monitor_thread.start()

while True:
    time.sleep(1)
