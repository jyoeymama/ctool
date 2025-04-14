#!/usr/bin/env python3

import os
import sys
import pwd
import grp
import getpass
import subprocess
import datetime
import re
import curses
from curses import panel

class MenuItem:
    def __init__(self, name, function):
        self.name = name
        self.function = function

class Menu:
    def __init__(self, items, stdscreen, title):
        self.window = stdscreen.subwin(0, 0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()
        
        self.position = 0
        self.items = items
        self.title = title
        
    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1
            
    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()
        
        # Get window dimensions
        height, width = self.window.getmaxyx()
        
        # Title bar
        self.window.attron(curses.color_pair(1))
        self.window.box()
        self.window.addstr(0, 2, f" {self.title} ")
        self.window.addstr(height-1, 2, " Press 'q' to exit ")
        self.window.attroff(curses.color_pair(1))
        
        # Print menu items
        for idx, item in enumerate(self.items):
            y = idx + 2
            if idx == self.position:
                mode = curses.A_REVERSE
            else:
                mode = curses.A_NORMAL
                
            msg = f"{idx+1}. {item.name}"
            self.window.addstr(y, 2, msg, mode)
            
        self.window.refresh()
        curses.doupdate()
        
    def execute(self):
        while True:
            self.display()
            key = self.window.getch()
            
            if key == curses.KEY_UP:
                self.navigate(-1)
            elif key == curses.KEY_DOWN:
                self.navigate(1)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                # User selected an option, clear screen and call function
                self.window.clear()
                self.window.refresh()
                self.items[self.position].function(self.window)
                self.window.clear()
                self.window.refresh()
            elif key == ord('q'):
                break
            
            # Number key shortcuts
            elif ord('1') <= key <= ord('9'):
                index = key - ord('1')
                if index < len(self.items):
                    self.position = index
                    self.window.clear()
                    self.window.refresh()
                    self.items[self.position].function(self.window)
                    self.window.clear()
                    self.window.refresh()
        
        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        
# Tool functions
def list_users(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "List of Users:", curses.A_BOLD)
    
    row = 3
    try:
        users = pwd.getpwall()
        for i, user in enumerate(users):
            if row >= curses.LINES - 2:  # Leave space for "Press any key" message
                break
                
            user_info = f"Username: {user.pw_name} | UID: {user.pw_uid} | GID: {user.pw_gid} | Shell: {user.pw_shell}"
            stdscr.addstr(row, 2, user_info[:curses.COLS-4])  # Truncate if too long
            row += 1
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def list_admin_users(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Users with Administrative Privileges:", curses.A_BOLD)
    
    row = 3
    try:
        # Check for sudo users and root group
        admin_users = set()
        
        # Check users in sudo/admin/wheel groups
        for group_name in ['sudo', 'admin', 'wheel', 'root']:
            try:
                group = grp.getgrnam(group_name)
                for user in group.gr_mem:
                    admin_users.add(user)
            except KeyError:
                pass
                
        # Add root user
        admin_users.add('root')
        
        # Check if we're on Linux with sudo
        if os.path.exists('/etc/sudoers'):
            try:
                # This would need root privileges, so it might not work
                result = subprocess.run(['grep', '-l', 'ALL=(ALL)', '/etc/sudoers', '/etc/sudoers.d/*'], 
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    stdscr.addstr(row, 2, "Sudo users detected (full details require root privileges)")
                    row += 1
            except Exception:
                pass
        
        for i, user in enumerate(sorted(admin_users)):
            try:
                user_info = pwd.getpwnam(user)
                stdscr.addstr(row, 2, f"Admin User: {user} | UID: {user_info.pw_uid} | Shell: {user_info.pw_shell}")
                row += 1
            except KeyError:
                stdscr.addstr(row, 2, f"Admin User: {user} (No additional info available)")
                row += 1
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def check_login_attempts(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Recent Login Attempts:", curses.A_BOLD)
    
    row = 3
    try:
        # Check auth.log on Linux or security logs on other systems
        log_files = [
            '/var/log/auth.log',
            '/var/log/secure', 
            '/var/log/security'
        ]
        
        found_log = False
        for log_file in log_files:
            if os.path.exists(log_file) and os.access(log_file, os.R_OK):
                found_log = True
                stdscr.addstr(row, 2, f"Reading log file: {log_file}")
                row += 1
                
                try:
                    with open(log_file, 'r') as f:
                        # Get the last 10 authentication lines
                        auth_lines = []
                        for line in f:
                            if 'sshd' in line and ('Failed' in line or 'Accepted' in line):
                                auth_lines.append(line.strip())
                                if len(auth_lines) > 10:
                                    auth_lines.pop(0)
                        
                        if auth_lines:
                            for line in auth_lines:
                                if row < curses.LINES - 2:
                                    truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                                    stdscr.addstr(row, 2, truncated)
                                    row += 1
                        else:
                            stdscr.addstr(row, 2, "No recent SSH login attempts found in logs.")
                            row += 1
                except Exception as e:
                    stdscr.addstr(row, 2, f"Error reading log: {str(e)}")
                    row += 1
                    
                break
        
        if not found_log:
            if sys.platform == 'win32':
                stdscr.addstr(row, 2, "On Windows, use Event Viewer to check Security logs (requires admin rights)")
                row += 1
            else:
                stdscr.addstr(row, 2, "Could not access authentication logs (may need root privileges)")
                row += 1
                
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def check_running_processes(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Suspicious Running Processes:", curses.A_BOLD)
    
    row = 3
    try:
        # Get running processes
        if sys.platform == 'win32':
            result = subprocess.run(['tasklist'], stdout=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
            
        lines = result.stdout.splitlines()
        
        # Keywords that might indicate suspicious activity
        suspicious_keywords = [
            'nc ', 'netcat', 'ncat',     # Netcat might be used for reverse shells
            'python -m SimpleHTTP',      # Web server often used by attackers
            'wget http', 'curl http',    # Downloading files from web
            'chmod 777',                 # Changing permissions
            'miner', 'xmr',              # Cryptocurrency miners
            'backdoor', 'rootkit',       # Obvious malware keywords
            'nmap', 'masscan',           # Scanning tools
            'metasploit', 'msfconsole'   # Penetration testing frameworks
        ]
        
        suspicious_found = False
        for line in lines[1:]:  # Skip header line
            if any(keyword in line.lower() for keyword in suspicious_keywords):
                suspicious_found = True
                if row < curses.LINES - 2:
                    truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                    stdscr.addstr(row, 2, truncated)
                    row += 1
        
        if not suspicious_found:
            stdscr.addstr(row, 2, "No obviously suspicious processes detected.")
            row += 1
            
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def check_network_connections(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Active Network Connections:", curses.A_BOLD)
    
    row = 3
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano'], stdout=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(['netstat', '-tunapl'], stdout=subprocess.PIPE, text=True)
            
        lines = result.stdout.splitlines()
        
        for i, line in enumerate(lines):
            if i > 0 and row < curses.LINES - 2:  # Skip header, check screen space
                truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                stdscr.addstr(row, 2, truncated)
                row += 1
                
                if row >= curses.LINES - 2:
                    stdscr.addstr(row, 2, "... (more connections available but not shown)")
                    row += 1
                    break
                    
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def check_open_ports(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Open Ports on System:", curses.A_BOLD)
    
    row = 3
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['netstat', '-an'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(['ss', '-tuln'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
        lines = result.stdout.splitlines()
        
        for i, line in enumerate(lines):
            if i > 0 and row < curses.LINES - 2:  # Skip header
                if 'LISTEN' in line or ('0.0.0.0' in line and 'LISTEN' in line):
                    truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                    stdscr.addstr(row, 2, truncated)
                    row += 1
                    
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def check_sudo_usage(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Recent Sudo Usage:", curses.A_BOLD)
    
    row = 3
    try:
        # Try to read sudo logs
        sudo_log_found = False
        
        if os.path.exists('/var/log/auth.log') and os.access('/var/log/auth.log', os.R_OK):
            sudo_log_found = True
            stdscr.addstr(row, 2, "Reading sudo entries from /var/log/auth.log")
            row += 1
            
            # Use grep to find sudo entries
            result = subprocess.run(['grep', 'sudo', '/var/log/auth.log'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                for line in lines[-10:]:  # Only show last 10 entries
                    if row < curses.LINES - 2:
                        truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                        stdscr.addstr(row, 2, truncated)
                        row += 1
            else:
                stdscr.addstr(row, 2, "No sudo entries found in logs.")
                row += 1
                
        elif os.path.exists('/var/log/secure') and os.access('/var/log/secure', os.R_OK):
            sudo_log_found = True
            stdscr.addstr(row, 2, "Reading sudo entries from /var/log/secure")
            row += 1
            
            # Use grep to find sudo entries
            result = subprocess.run(['grep', 'sudo', '/var/log/secure'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                for line in lines[-10:]:  # Only show last 10 entries
                    if row < curses.LINES - 2:
                        truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                        stdscr.addstr(row, 2, truncated)
                        row += 1
            else:
                stdscr.addstr(row, 2, "No sudo entries found in logs.")
                row += 1
                
        if not sudo_log_found:
            stdscr.addstr(row, 2, "Could not access sudo logs (may need root privileges)")
            row += 1
            
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def check_cron_jobs(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Scheduled Tasks/Cron Jobs:", curses.A_BOLD)
    
    row = 3
    try:
        if sys.platform != 'win32':  # Linux/Unix
            # System crontabs
            stdscr.addstr(row, 2, "System Crontabs:", curses.A_UNDERLINE)
            row += 1
            
            # Check /etc/crontab
            if os.path.exists('/etc/crontab') and os.access('/etc/crontab', os.R_OK):
                stdscr.addstr(row, 2, "From /etc/crontab:")
                row += 1
                
                with open('/etc/crontab', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if row < curses.LINES - 2:
                                truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                                stdscr.addstr(row, 2, truncated)
                                row += 1
            
            # Check cron.d directory
            if os.path.exists('/etc/cron.d') and os.access('/etc/cron.d', os.R_OK):
                stdscr.addstr(row, 2, "From /etc/cron.d:")
                row += 1
                
                for cron_file in os.listdir('/etc/cron.d'):
                    file_path = os.path.join('/etc/cron.d', cron_file)
                    if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                        if row < curses.LINES - 2:
                            stdscr.addstr(row, 2, f"File: {cron_file}")
                            row += 1
                            
                            with open(file_path, 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        if row < curses.LINES - 2:
                                            truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                                            stdscr.addstr(row, 2, f"  {truncated}")
                                            row += 1
                
            # Try to view current user's crontab
            result = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0 and result.stdout.strip():
                stdscr.addstr(row, 2, f"User {getpass.getuser()} Crontab:", curses.A_UNDERLINE)
                row += 1
                
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if row < curses.LINES - 2:
                            truncated = line[:curses.COLS-5] + ('...' if len(line) > curses.COLS-5 else '')
                            stdscr.addstr(row, 2, truncated)
                            row += 1
        else:  # Windows
            stdscr.addstr(row, 2, "On Windows, use 'schtasks' command to view scheduled tasks.")
            row += 1
            
            result = subprocess.run(['schtasks', '/query', '/fo', 'list'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                task_sections = result.stdout.split('\n\n')
                for section in task_sections:
                    if 'TaskName:' in section and row < curses.LINES - 2:
                        task_lines = section.splitlines()
                        task_name = next((line.split(':', 1)[1].strip() for line in task_lines 
                                        if line.startswith('TaskName:')), 'Unknown')
                        
                        stdscr.addstr(row, 2, f"Task: {task_name}")
                        row += 1
                        
                        # Show command if available
                        command = next((line.split(':', 1)[1].strip() for line in task_lines 
                                      if 'Task To Run:' in line or 'Application Name:' in line), 'Unknown')
                        
                        if row < curses.LINES - 2:
                            truncated = f"Command: {command}"[:curses.COLS-5] + ('...' if len(f"Command: {command}") > curses.COLS-5 else '')
                            stdscr.addstr(row, 2, truncated)
                            row += 1
            else:
                stdscr.addstr(row, 2, "Could not get scheduled tasks (may need admin privileges)")
                row += 1
                
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def check_file_integrity(stdscr):
    stdscr.clear()
    stdscr.addstr(1, 1, "Critical System File Check:", curses.A_BOLD)
    
    row = 3
    try:
        critical_paths = [
            '/bin/bash', '/bin/sh', '/bin/ls', '/bin/login',
            '/usr/bin/sudo', '/etc/passwd', '/etc/shadow', '/etc/sudoers'
        ]
        
        if sys.platform == 'win32':
            critical_paths = [
                'C:\\Windows\\System32\\cmd.exe',
                'C:\\Windows\\System32\\powershell.exe',
                'C:\\Windows\\System32\\taskmgr.exe',
                'C:\\Windows\\System32\\services.exe'
            ]
        
        for path in critical_paths:
            if os.path.exists(path):
                stats = os.stat(path)
                modified_time = datetime.datetime.fromtimestamp(stats.st_mtime)
                
                # Format the output
                if row < curses.LINES - 2:
                    stdscr.addstr(row, 2, f"File: {path}")
                    row += 1
                if row < curses.LINES - 2:
                    stdscr.addstr(row, 2, f"  Size: {stats.st_size} bytes | Modified: {modified_time}")
                    row += 1
                if row < curses.LINES - 2:
                    stdscr.addstr(row, 2, f"  Permissions: {oct(stats.st_mode)[-3:]}")
                    row += 1
            else:
                if row < curses.LINES - 2:
                    stdscr.addstr(row, 2, f"WARNING: Critical file {path} not found!")
                    row += 1
                    
    except Exception as e:
        stdscr.addstr(row, 2, f"Error: {str(e)}")
        
    stdscr.addstr(curses.LINES-1, 1, "Press any key to return to menu...", curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()

def main(stdscr):
    # Setup colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    
    # Hide cursor
    curses.curs_set(0)
    
    # Create menu items
    menu_items = [
        MenuItem("List All Users", list_users),
        MenuItem("List Admin Users", list_admin_users),
        MenuItem("Check Login Attempts", check_login_attempts),
        MenuItem("Check Running Processes", check_running_processes),
        MenuItem("Check Network Connections", check_network_connections),
        MenuItem("Check Open Ports", check_open_ports),
        MenuItem("Check Sudo Usage", check_sudo_usage),
        MenuItem("Check Scheduled Tasks/Cron Jobs", check_cron_jobs),
        MenuItem("Check Critical System Files", check_file_integrity)
    ]
    
    # Create the menu
    menu = Menu(menu_items, stdscr, "Blue Hat Hacker Toolkit")
    
    # Show the menu
    menu.execute()

if __name__ == "__main__":
    try:
        # Initialize curses
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("Program terminated by user.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
