import requests
import tkinter as tk
from tkinter import messagebox
import threading
import psutil
import time
from datetime import datetime

class CaptureThread(threading.Thread):
    RUNNING_STATUS = 1
    PAUSED_STATUS = 2
    STOPPED_STATUS = 3
    RESUMED_STATUS = 4
    def __init__(self, user_id, status, sleep_time, productive_apps):
        super().__init__()
        self.user_id = str(user_id)
        self.status = status
        self.pause_time = 0
        self.resume_time = 0
        self.sleep_time = sleep_time
        self._stop_event = threading.Event()
        self.productive_apps = productive_apps  # Diccionario de apps productivas y sus nombres amigables
        self.process_start_times = {app: None for app in self.productive_apps}
        self.productive_time = {app: 0 for app in self.productive_apps}
        self.points = {app: 0 for app in self.productive_apps}
        self.captured_activities = []
        self.sensor_endpoint_id = "7"
    
    def set_status(self, status):
        if status == self.PAUSED_STATUS:
            self.pause_time = datetime.now().timestamp()
        elif status == self.RESUMED_STATUS:
            self.resume_time = datetime.now().timestamp()
        self.status = status
        
    def stop(self):
        self._stop_event.set()
    
    def run(self):
        while not self._stop_event.is_set():
            if self.status in [self.RUNNING_STATUS, self.RESUMED_STATUS]:
                processes = [proc for proc in psutil.process_iter(['pid', 'name', 'username'])]
                now = datetime.now().timestamp()
                resumed_capture_time = self.pause_time + (now - self.resume_time)
                capture_time = now if self.resume_time == 0 else resumed_capture_time
                
                self.update_productive_time(processes, capture_time)
                
                time.sleep(self.sleep_time)
            elif self.status == self.PAUSED_STATUS:
                time.sleep(0.2)
            elif self.status == self.STOPPED_STATUS:
                self.calculate_final_times()
                return
    
    def update_productive_time(self, processes, current_time):
        running_apps = {app: False for app in self.productive_apps}
        
        for proc in processes:
            try:
                pinfo = proc.info
                app_name = pinfo['name']
                if app_name in self.productive_apps:
                    running_apps[app_name] = True
                    if self.process_start_times[app_name] is None:
                        self.process_start_times[app_name] = current_time
                        if app_name not in self.captured_activities:  # Asegúrate de no agregar duplicados
                            self.captured_activities.append(app_name)  # Añadir actividad capturada
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        for app in self.productive_apps:
            if running_apps[app]:
                if self.process_start_times[app] is not None:
                    self.productive_time[app] += current_time - self.process_start_times[app]
                self.process_start_times[app] = current_time
            else:
                self.process_start_times[app] = None
        
        self.award_points()
        #print(f"Productive time so far: {self.productive_time}, Points: {self.points}")

    def award_points(self):
        for app, time_spent in self.productive_time.items():
            new_points = int(time_spent // 60) - self.points[app]  # Puntos nuevos desde la última vez (puntos cada 60 segundos (1 min.))
            if new_points > 0:
                self.points[app] += new_points
                self.send_points_to_server(new_points)
    
    def send_points_to_server(self, total_points):
        url = "http://localhost:3002/adquired_subattribute/"
        data = {
            "id_player": self.user_id,
            "id_subattributes_conversion_sensor_endpoint": self.sensor_endpoint_id,
            "new_data": [str(total_points)]
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Puntos enviados exitosamente: {total_points}")
            else:
                messagebox.showerror("Error", f"Failed to send points: {response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while sending points: {e}")

        
    def calculate_final_times(self):
        final_times = {app: 0 for app in self.productive_apps}
        current_time = datetime.now().timestamp()
        
        for app in self.productive_apps:
            if self.process_start_times[app] is not None:
                final_times[app] = self.productive_time[app] + (current_time - self.process_start_times[app])
            else:
                final_times[app] = self.productive_time[app]
        
        #print(f"Final productive times: {final_times}, Final Points: {self.points}")

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Login bGames")
        self.root.geometry("300x200")
        self.user_id = None
        self.productive_apps = {}  # Aquí se almacenará la lista de aplicaciones productivas obtenidas del servidor
        self.create_login_widgets()
        self.capture_thread = None

    def create_login_widgets(self):
        self.label_username = tk.Label(self.root, text="Username")
        self.label_username.pack(pady=10)
        
        self.entry_username = tk.Entry(self.root, width=30)
        self.entry_username.pack(pady=5)
        
        self.label_password = tk.Label(self.root, text="Password")
        self.label_password.pack(pady=10)
        
        self.entry_password = tk.Entry(self.root, show="*", width=30)
        self.entry_password.pack(pady=5)
        
        self.button_login = tk.Button(self.root, text="Login", command=self.login, width=10)
        self.button_login.pack(pady=20)
        
    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        
        if username and password:
            try:
                user_id = self.authenticate_user(username, password)
                if user_id:
                    self.user_id = user_id  # Almacenar el userID
                    self.root.withdraw()
                    self.load_productive_apps()  # Cargar las aplicaciones productivas desde el servidor
                    self.open_main_app()
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred during login: {e}")
        else:
            messagebox.showerror("Error", "Username or password cannot be empty.")

    
    def authenticate_user(self, username, password):
        try:
            response = requests.get(f"http://localhost:3010/player/{username}/{password}")
            if response.status_code == 200:
                return response.json()  # Asume que el servidor devuelve solo el userID
            else:
                messagebox.showerror("Authentication Error", "Invalid credentials or unable to reach the server.")
                return None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to the server")
            return None
    
    def load_productive_apps(self):
        try:
            response = requests.get("http://localhost:5001/productive_apps")
            if response.status_code == 200:
                self.productive_apps = response.json()
            else:
                messagebox.showerror("Error", f"Failed to load productive apps: {response.status_code} - {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading productive apps: {e}")

    
    def open_main_app(self):
        main_app_window = tk.Toplevel(self.root)
        main_app_window.title("Process Activity Sensor")
        
        self.label_info = tk.Label(main_app_window, text=f"Capturando actividades del sistema...")
        self.label_info.pack()
        
        self.listbox_activities = tk.Listbox(main_app_window)
        self.listbox_activities.pack(fill=tk.BOTH, expand=True)
        
        # Inicia el hilo de captura pasándole las aplicaciones productivas y sus nombres amigables
        self.capture_thread = CaptureThread(self.user_id, CaptureThread.RUNNING_STATUS, 0.2, self.productive_apps)
        self.capture_thread.start()
        
        self.update_activity_list()
        main_app_window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_activity_list(self):
        if self.capture_thread and self.capture_thread.is_alive():
            self.listbox_activities.delete(0, tk.END)
            now = datetime.now().timestamp()
            displayed_apps = set()  # Mantener un seguimiento de las aplicaciones ya mostradas
            for activity in self.capture_thread.captured_activities:
                start_time = self.capture_thread.process_start_times[activity]
                if start_time:
                    time_spent = self.capture_thread.productive_time[activity] + (now - start_time)
                else:
                    time_spent = self.capture_thread.productive_time[activity]
                
                points = self.capture_thread.points[activity]
                formatted_time = f"{int(time_spent // 3600):02}:{int((time_spent % 3600) // 60):02}:{int(time_spent % 60):02}"
                
                # Obtener el nombre amigable de la aplicación
                app_name = self.capture_thread.productive_apps.get(activity, activity)
                
                if activity not in displayed_apps:  # Evita mostrar duplicados
                    self.listbox_activities.insert(tk.END, f"{app_name}: {formatted_time} (Points: {points})")
                    displayed_apps.add(activity)
            
            self.root.after(200, self.update_activity_list)

    def on_closing(self):
        if self.capture_thread:
            self.capture_thread.set_status(CaptureThread.STOPPED_STATUS)
            self.capture_thread.stop()
            self.capture_thread.join()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
