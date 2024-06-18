import psutil
import json
import csv
import threading
import time
from datetime import datetime

class CaptureThread(threading.Thread):
    RUNNING_STATUS = 1
    PAUSED_STATUS = 2
    STOPPED_STATUS = 3
    RESUMED_STATUS = 4
    
    def __init__(self, status, output_files, sleep_time):
        super().__init__()
        self.status = status
        self.pause_time = 0
        self.resume_time = 0
        self.sleep_time = sleep_time
        self.output_files = output_files
        self._stop_event = threading.Event()
        
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
                processes = [proc for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_times', 'cmdline', 'ppid'])]
                now = datetime.now().timestamp()
                resumed_capture_time = self.pause_time + (now - self.resume_time)
                capture_time = now if self.resume_time == 0 else resumed_capture_time
                snapshot = self.processes_to_snapshot(processes, capture_time)
                
                for output_file in self.output_files:
                    to_write = ""
                    if output_file['format'] == 'json':
                        to_write = json.dumps(snapshot) + '\n'
                    elif output_file['format'] == 'csv':
                        to_write = self.snapshot_to_csv(snapshot)
                    
                    try:
                        with open(output_file['path'], 'a') as f:
                            f.write(to_write)
                    except IOError as e:
                        print(f"Error writing to file: {e}")
                        return
                
                time.sleep(self.sleep_time)
            elif self.status == self.PAUSED_STATUS:
                time.sleep(0.5)
            elif self.status == self.STOPPED_STATUS:
                return
    
    def processes_to_snapshot(self, processes, capture_time):
        processes_list = []
        for proc in processes:
            try:
                pinfo = proc.info
                process_info = {
                    'pid': pinfo['pid'],
                    'captureTime': capture_time,
                    'userName': pinfo.get('username', ''),
                    'startInstant': proc.create_time(),
                    'totalCpuDuration': pinfo['cpu_times'].user + pinfo['cpu_times'].system,
                    'command': ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else '',
                    'parentPid': pinfo['ppid'],
                    'hasChildren': len(proc.children()) > 0
                }
                processes_list.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        snapshot = {
            'processes': processes_list,
            'captureTimestamp': capture_time
        }
        return snapshot
    
    def snapshot_to_csv(self, snapshot):
        csv_output = ""
        headers = "pid,captureTime,userName,startInstant,totalCpuDuration,command,parentPid,hasChildren"
        csv_output += headers + '\n'
        for process in snapshot['processes']:
            row = f"{process['pid']},{process['captureTime']},{process['userName']},{process['startInstant']},{process['totalCpuDuration']},{process['command']},{process['parentPid']},{process['hasChildren']}"
            csv_output += row + '\n'
        return csv_output

if __name__ == "__main__":
    output_files = [
        {'format': 'json', 'path': 'processes.json'},
        {'format': 'csv', 'path': 'processes.csv'}
    ]
    capture_thread = CaptureThread(CaptureThread.RUNNING_STATUS, output_files, 5)
    capture_thread.start()
    
    # Simulate status changes
    time.sleep(10)
    capture_thread.set_status(CaptureThread.PAUSED_STATUS)
    time.sleep(5)
    capture_thread.set_status(CaptureThread.RESUMED_STATUS)
    time.sleep(10)
    capture_thread.set_status(CaptureThread.STOPPED_STATUS)
    
    capture_thread.join()
