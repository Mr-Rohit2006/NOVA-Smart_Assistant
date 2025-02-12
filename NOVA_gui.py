import tkinter as tk
from tkinter import Label
import threading
import speech_recognition as sr
import pyttsx3
import pyaudio
import pyautogui
import webbrowser
import psutil
import requests
import re
from datetime import datetime
import time
import cv2

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 160)

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def listen():
    """Capture voice command."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        status_label.config(text="Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            status_label.config(text=f"You said: {command}")
            return command
        except sr.UnknownValueError:
            status_label.config(text="Could not understand, try again.")
            speak("Sorry, I couldn't understand.")
            return None
        except sr.RequestError:
            status_label.config(text="Network error!")
            speak("Network error. Please check your internet connection.")
            return None

def check_battery():
    """Check battery percentage and status."""
    battery = psutil.sensors_battery()
    percent = battery.percent
    plugged = battery.power_plugged

    if plugged:
        speak(f"The battery is at {percent} percent and is currently charging.")
    else:
        speak(f"The battery is at {percent} percent and is not charging.")

def check_disk_space():
    """Check and announce the disk space."""
    disk_usage = psutil.disk_usage('/')
    total = disk_usage.total / (1024**3)
    used = disk_usage.used / (1024**3)
    free = disk_usage.free / (1024**3)

    response = f"Total disk space: {total:.2f} GB. Used: {used:.2f} GB. Free: {free:.2f} GB."
    speak(response)

def get_time():
    """Fetch and announce the current time."""
    current_time = datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}")

def get_date():
    """Fetch and announce the current date."""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today's date is {current_date}")

def show_exit_screen():
    """Display a full-screen exit message before closing."""
    exit_screen = tk.Toplevel(root)
    exit_screen.attributes('-fullscreen', True)
    exit_screen.configure(bg="black")

    exit_label = tk.Label(exit_screen, text="👋 Goodbye!", font=("Arial", 50), fg="white", bg="black")
    exit_label.pack(expand=True)

    root.after(2000, root.destroy)  # Close after 3 seconds


def get_weather(command):
    """Fetch weather information dynamically based on user input."""
    
    # Default location (fallback)
    default_city = "New York"
    
    # Extract city name from the command
    match = re.search(r"weather in ([\w\s]+)", command)
    city = match.group(1) if match else default_city

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&APPID=bf3abca2bd46c995a5002a6f33a90948"
    
    try:
        response = requests.get(url).json()
        
        if response["cod"] == 200:
            temp = response["main"]["temp"]
            weather_desc = response["weather"][0]["description"]
            humidity = response["main"]["humidity"]
            wind_speed = response["wind"]["speed"]

            # Adding clear description of weather conditions
            speak(f"The weather in {city} is {weather_desc}. The temperature is {temp}°C, humidity is {humidity}%, and the wind speed is {wind_speed} meters per second.")
        else:
            speak(f"I couldn't find the weather for {city}. Please try again.")
    
    except requests.exceptions.RequestException:
        speak("Network error! Unable to fetch weather.")

def get_news():
    API_KEY = "e4317653a86f4cff9c53d6044e405841"
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}"
    
    response = requests.get(url).json()
    
    if response["status"] == "ok":
        articles = response["articles"][:5]  # Get top 5 headlines
        for article in articles:
            speak(article["title"])
    else:
        speak("Unable to fetch news at the moment.")

def set_reminder(task, delay):
    speak(f"Reminder set for {task} in {delay} seconds.")
    time.sleep(delay)
    speak(f"Reminder: {task}")
def capture_photo():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        cv2.imwrite("photo.jpg", frame)
        speak("Photo captured successfully.")
    cam.release()
    cv2.destroyAllWindows()

net = cv2.dnn.readNetFromCaffe("deploy.prototxt", "mobilenet_iter_73000.caffemodel")

# List of object categories in the model
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair","cup", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant",
           "sheep", "sofa", "train", "tvmonitor"]

def recognize_objects():
    """Capture image and detect objects."""
    cam = cv2.VideoCapture(0)

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        # Convert frame to blob for model input
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
        net.setInput(blob)
        detections = net.forward()
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:  # Only detect if confidence > 50%
                idx = int(detections[0, 0, i, 1])  # Object class index
                label = CLASSES[idx]  # Get class name
                
                # Draw bounding box
                box = detections[0, 0, i, 3:7] * np.array([frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
                (startX, startY, endX, endY) = box.astype("int")
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                cv2.putText(frame, label, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Speak detected object
                speak(f"I see a {label}")

        cv2.imshow("Object Recognition", frame)
        
        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

def execute_command(command):
    """Perform actions based on commands."""
    if not command:
        return

    if "exit" in command:
        speak("Goodbye! Have a great day!")
        show_exit_screen()
    elif "open browser" in command:
        speak("Opening browser")
        webbrowser.open("https://www.google.com")
    elif "take screenshot" in command:
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        speak("Screenshot saved.")
    elif "volume up" in command:
        pyautogui.press("volumeup")
        speak("Increasing volume.")
    elif "volume down" in command:
        pyautogui.press("volumedown")
        speak("Decreasing volume.")
    elif "mute" in command:
        pyautogui.press("volumemute")
        speak("Muting volume.")
    elif "youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
    elif "songs" in command:
        speak("Opening Spotify")
        webbrowser.open("https://www.spotify.com")
    elif "battery" in command:
        check_battery()
    elif "check space" in command or "storage" in command:
        check_disk_space()
    elif "what time is it" in command or "current time" in command:
        get_time()
    elif "what's the date" in command or "today's date" in command:
        get_date()
    elif "weather" in command:
        get_weather(command)
    elif "news" in command:
        get_news()
    elif "remind me" in command:
        words = command.split()
        task = " ".join(words[2:-2])  # Extract task name
        delay = int(words[-2])  # Extract time in seconds
        threading.Thread(target=set_reminder, args=(task, delay), daemon=True).start()
    elif "take a picture" in command:
        capture_photo()
    elif "recognize object" in command or "what is this" in command:
        recognize_objects()
    else:
        speak("Command not recognized.")

def start_listening():
    """Start listening in a new thread to avoid GUI freezing."""
    threading.Thread(target=lambda: execute_command(listen()), daemon=True).start()

# Create GUI Window
root = tk.Tk()
root.title("NOVA - Smart Assistant")
root.geometry("450x400")
root.configure(bg="#2c3e50")

status_label = Label(root, text="Press the button and speak", font=("Arial", 12), fg="white", bg="#2c3e50")
status_label.pack(pady=20)

listen_button = tk.Button(root, text="🎤 Start Listening", command=start_listening, font=("Arial", 14), bg="#27ae60", fg="white")
listen_button.pack(pady=10)

root.mainloop()
