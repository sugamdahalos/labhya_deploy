#!/usr/bin/env python3
"""
GUI Launcher for Labhya GPU Agent
Provides a simple GUI interface for configuring and launching the agent
"""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

import os
import sys
import threading
import subprocess
import logging
from pathlib import Path
from combined_agent import AgentCore, SystemChecker

class AgentGUI:
    """GUI for the Labhya GPU Agent"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Labhya GPU Agent")
        self.root.geometry("700x600")
        
        self.agent = None
        self.agent_thread = None
        self.logged_in = False
        self.host_registered = False
        self.gpu_registered = False
        
        # State variables
        self.login_frame = None
        self.main_frame = None
        
        self.setup_login_gui()
    
    def setup_login_gui(self):
        """Setup the login interface"""
        # Clear any existing frames
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_container, text="Labhya GPU Agent", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Login frame
        self.login_frame = ttk.LabelFrame(main_container, text="Login", padding="20")
        self.login_frame.pack(fill="x", pady=10)
        
        # Server URL
        ttk.Label(self.login_frame, text="Server URL:").grid(row=0, column=0, sticky="w", pady=5)
        self.server_var = tk.StringVar(value=os.getenv('LABHYA_API_URL', 'http://localhost:8000'))
        ttk.Entry(self.login_frame, textvariable=self.server_var, width=50).grid(row=0, column=1, sticky="ew", pady=5)
        
        # Email
        ttk.Label(self.login_frame, text="Email:").grid(row=1, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar(value=os.getenv('LABHYA_AGENT_EMAIL', ''))
        ttk.Entry(self.login_frame, textvariable=self.email_var, width=50).grid(row=1, column=1, sticky="ew", pady=5)
        
        # Password
        ttk.Label(self.login_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=5)
        self.password_var = tk.StringVar(value=os.getenv('LABHYA_AGENT_PASSWORD', ''))
        self.password_entry = ttk.Entry(self.login_frame, textvariable=self.password_var, show="*", width=50)
        self.password_entry.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Login button
        self.login_btn = ttk.Button(self.login_frame, text="Login", command=self.login)
        self.login_btn.grid(row=3, column=1, sticky="e", pady=10)
        
        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda event: self.login())
        
        self.login_frame.columnconfigure(1, weight=1)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_container, text="System Status", padding="10")
        status_frame.pack(fill="x", pady=10)
        
        self.status_text = tk.Text(status_frame, height=6, wrap=tk.WORD, state='disabled')
        self.status_text.pack(fill="both", expand=True)
        
        # Check requirements button
        check_frame = ttk.Frame(main_container)
        check_frame.pack(fill="x", pady=5)
        
        ttk.Button(check_frame, text="Check System Requirements", 
                  command=self.check_requirements).pack(side="left")
        
        # Initial requirements check
        self.check_requirements()
    
    def login(self):
        """Handle login process"""
        if not self.email_var.get() or not self.password_var.get():
            messagebox.showerror("Error", "Please enter both email and password")
            return
        
        if not self.server_var.get():
            messagebox.showerror("Error", "Please enter server URL")
            return
        
        # Disable login button during authentication
        self.login_btn.config(state="disabled", text="Logging in...")
        
        def authenticate():
            try:
                # Create HTTP client and authenticate
                from combined_agent import HTTPClient, GPUMonitor
                client = HTTPClient(self.server_var.get())
                
                if client.authenticate(self.email_var.get(), self.password_var.get()):
                    # Check if host is already registered and has GPUs
                    self.check_host_and_gpu_status(client)
                else:
                    self.root.after(0, lambda: self.login_failed("Authentication failed"))
                    
            except Exception as e:
                error_msg = f"Login error: {str(e)}"
                self.root.after(0, lambda msg=error_msg: self.login_failed(msg))
        
        # Run authentication in separate thread
        threading.Thread(target=authenticate, daemon=True).start()
    
    def check_host_and_gpu_status(self, client):
        """Check if host is registered and has GPUs"""
        try:
            # Check if host exists
            response = client.get(f"{self.server_var.get()}/api/hosts/current/")
            
            if response.status_code == 200:
                host_data = response.json()
                self.host_registered = True
                
                # Check if GPUs are registered for this host
                if host_data.get('gpu_count', 0) > 0:
                    self.gpu_registered = True
                    self.root.after(0, lambda: self.login_success(client, "Host and GPUs already registered"))
                else:
                    self.gpu_registered = False
                    self.root.after(0, lambda: self.login_success(client, "Host registered but no GPUs found"))
                    
            elif response.status_code == 404:
                # Host not registered
                self.host_registered = False
                self.gpu_registered = False
                self.root.after(0, lambda: self.login_success(client, "Host not registered"))
            else:
                error_msg = f"Server error: {response.status_code}"
                self.root.after(0, lambda msg=error_msg: self.login_failed(msg))
                
        except Exception as e:
            error_msg = f"Status check error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.login_failed(msg))
    
    def login_success(self, client, status_message):
        """Handle successful login"""
        self.logged_in = True
        
        # Store client for later use
        self.http_client = client
        
        # Update environment variables
        os.environ['LABHYA_API_URL'] = self.server_var.get()
        os.environ['LABHYA_AGENT_EMAIL'] = self.email_var.get()
        os.environ['LABHYA_AGENT_PASSWORD'] = self.password_var.get()
        
        messagebox.showinfo("Success", f"Login successful!\n{status_message}")
        
        # Switch to main agent interface
        self.setup_main_gui()
    
    def login_failed(self, error_message):
        """Handle failed login"""
        self.login_btn.config(state="normal", text="Login")
        messagebox.showerror("Login Failed", error_message)
    
    def setup_main_gui(self):
        """Setup the main agent interface after login"""
        # Clear login interface
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title with user info
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(title_frame, text="Labhya GPU Agent", font=("Arial", 16, "bold")).pack(side="left")
        ttk.Label(title_frame, text=f"Logged in as: {self.email_var.get()}", 
                 font=("Arial", 9)).pack(side="right")
        
        # Logout button
        ttk.Button(title_frame, text="Logout", command=self.logout).pack(side="right", padx=(5, 0))
        
        # GPU Status frame
        gpu_frame = ttk.LabelFrame(main_container, text="GPU Status", padding="10")
        gpu_frame.pack(fill="x", pady=5)
        
        self.gpu_status_text = tk.Text(gpu_frame, height=4, wrap=tk.WORD, state='disabled')
        self.gpu_status_text.pack(fill="both", expand=True)
        
        # Control buttons frame
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill="x", pady=10)
        
        if self.gpu_registered:
            # Show Start/Stop Agent buttons
            self.start_btn = ttk.Button(button_frame, text="Start Agent", command=self.start_agent)
            self.start_btn.pack(side="left", padx=5)
            
            self.stop_btn = ttk.Button(button_frame, text="Stop Agent", command=self.stop_agent, state="disabled")
            self.stop_btn.pack(side="left", padx=5)
        else:
            # Show Register GPU button
            self.register_gpu_btn = ttk.Button(button_frame, text="Register GPU", command=self.register_gpu)
            self.register_gpu_btn.pack(side="left", padx=5)
        
        # Refresh button
        ttk.Button(button_frame, text="Refresh Status", command=self.refresh_status).pack(side="left", padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_container, text="Agent Log", padding="10")
        log_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)
        
        # Setup logging redirection
        self.setup_logging()
        
        # Initial status check
        self.refresh_status()
    
    def setup_logging(self):
        """Setup logging redirection to GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    try:
                        if self.text_widget.winfo_exists():
                            self.text_widget.insert(tk.END, msg + '\n')
                            self.text_widget.see(tk.END)
                    except (tk.TclError, AttributeError):
                        # Widget was destroyed, ignore
                        pass
                try:
                    self.text_widget.after(0, append)
                except (tk.TclError, AttributeError):
                    # Widget was destroyed, ignore
                    pass
        
        handler = GUILogHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def register_gpu(self):
        """Register GPU with the backend"""
        self.register_gpu_btn.config(state="disabled", text="Registering...")
        
        def register():
            try:
                from combined_agent import AgentCore
                agent = AgentCore(self.server_var.get(), use_signal_handlers=False)
                
                # Set credentials for the agent
                agent.http_client = self.http_client
                
                if agent.register_host():
                    self.gpu_registered = True
                    self.root.after(0, lambda: self.registration_success())
                else:
                    self.root.after(0, lambda: self.registration_failed("Failed to register GPU"))
                    
            except Exception as e:
                error_msg = f"Registration error: {str(e)}"
                self.root.after(0, lambda msg=error_msg: self.registration_failed(msg))
        
        threading.Thread(target=register, daemon=True).start()
    
    def registration_success(self):
        """Handle successful GPU registration"""
        messagebox.showinfo("Success", "GPU registered successfully!")
        # Refresh the main GUI to show agent controls
        self.setup_main_gui()
    
    def registration_failed(self, error_message):
        """Handle failed GPU registration"""
        self.register_gpu_btn.config(state="normal", text="Register GPU")
        messagebox.showerror("Registration Failed", error_message)
    
    def refresh_status(self):
        """Refresh GPU and system status"""
        def update_status():
            try:
                from combined_agent import GPUMonitor, SystemChecker
                
                # Get GPU info
                gpus = GPUMonitor.get_gpu_info()
                
                # Get system requirements
                requirements = SystemChecker.check_system_requirements()
                
                status_text = f"System Requirements: {requirements['message']}\n\n"
                
                if gpus:
                    status_text += f"Detected GPUs ({len(gpus)}):\n"
                    for gpu in gpus:
                        status_text += f"  • {gpu['name']} - {gpu['memory_used']}/{gpu['memory_total']} MB\n"
                        status_text += f"    Utilization: {gpu['utilization']}%, Temperature: {gpu['temperature']}°C\n"
                else:
                    status_text += "No GPUs detected\n"
                
                def update_gui():
                    self.gpu_status_text.config(state='normal')
                    self.gpu_status_text.delete(1.0, tk.END)
                    self.gpu_status_text.insert(1.0, status_text)
                    self.gpu_status_text.config(state='disabled')
                
                self.root.after(0, update_gui)
                
            except Exception as e:
                def show_error():
                    self.gpu_status_text.config(state='normal')
                    self.gpu_status_text.delete(1.0, tk.END)
                    self.gpu_status_text.insert(1.0, f"Error getting status: {str(e)}")
                    self.gpu_status_text.config(state='disabled')
                
                self.root.after(0, show_error)
        
        threading.Thread(target=update_status, daemon=True).start()
    
    def logout(self):
        """Handle logout"""
        if self.agent and self.agent.running:
            if messagebox.askokcancel("Logout", "Agent is running. Stop it and logout?"):
                self.stop_agent()
            else:
                return
        
        self.logged_in = False
        self.host_registered = False
        self.gpu_registered = False
        self.http_client = None
        
        messagebox.showinfo("Logout", "Logged out successfully")
        self.setup_login_gui()
    
    def check_requirements(self):
        """Check system requirements"""
        def check():
            try:
                from combined_agent import SystemChecker
                requirements = SystemChecker.check_system_requirements()
                
                status_lines = [f"System Requirements Check: {requirements['message']}\n"]
                
                checks = [
                    ("WSL2 Enabled", requirements['wsl_ok']),
                    ("Ubuntu Installed", requirements['ubuntu_ok']),
                    ("Docker Installed", requirements['docker_installed']),
                    ("Docker Running", requirements['docker_running'])
                ]
                
                for name, status in checks:
                    icon = "✓" if status else "✗"
                    status_lines.append(f"{icon} {name}")
                
                status_text = "\n".join(status_lines)
                
                def update_gui():
                    self.status_text.config(state='normal')
                    self.status_text.delete(1.0, tk.END)
                    self.status_text.insert(1.0, status_text)
                    self.status_text.config(state='disabled')
                
                self.root.after(0, update_gui)
                
            except Exception as e:
                def show_error():
                    self.status_text.config(state='normal')
                    self.status_text.delete(1.0, tk.END)
                    self.status_text.insert(1.0, f"Error checking requirements: {str(e)}")
                    self.status_text.config(state='disabled')
                
                self.root.after(0, show_error)
        
        threading.Thread(target=check, daemon=True).start()
    
    def start_agent(self):
        """Start the agent"""
        if not self.logged_in:
            messagebox.showerror("Error", "Please login first")
            return
        
        # Update GUI state
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        def run_agent():
            try:
                from combined_agent import AgentCore
                self.agent = AgentCore(self.server_var.get(), use_signal_handlers=False)
                
                # Use existing authenticated client
                self.agent.http_client = self.http_client
                
                # Skip authentication since we're already logged in
                self.agent.host_id = getattr(self.http_client, 'host_id', None)
                
                if self.agent.start(skip_auth=True):
                    # Keep running until stopped
                    while self.agent.running:
                        if not self.agent_thread or not self.agent_thread.is_alive():
                            break
                        threading.Event().wait(1)
                else:
                    error_msg = "Failed to start agent"
                    self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                    
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("Error", f"Agent error: {error_msg}"))
            finally:
                self.root.after(0, self._agent_stopped)
        
        self.agent_thread = threading.Thread(target=run_agent)
        self.agent_thread.daemon = True
        self.agent_thread.start()
        
        self.log_text.insert(tk.END, "Starting agent...\n")
        self.log_text.see(tk.END)
    
    def stop_agent(self):
        """Stop the agent"""
        if self.agent:
            self.agent.stop()
        
        self._agent_stopped()
    
    def _agent_stopped(self):
        """Called when agent stops"""
        if hasattr(self, 'start_btn') and hasattr(self, 'stop_btn'):
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
        
        self.log_text.insert(tk.END, "Agent stopped.\n")
        self.log_text.see(tk.END)
    
    def on_closing(self):
        """Handle window closing"""
        if self.agent and self.agent.running:
            if messagebox.askokcancel("Quit", "Agent is running. Stop it and quit?"):
                self.stop_agent()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main entry point for GUI launcher"""
    if not GUI_AVAILABLE:
        print("GUI not available. Install tkinter or run combined_agent.py directly.")
        print("Running in headless mode...")
        
        # Import and run the headless agent
        from combined_agent import main as agent_main
        agent_main()
        return
    
    # Check if running in headless mode
    if '--headless' in sys.argv:
        from combined_agent import main as agent_main
        agent_main()
        return
    
    # Run GUI
    root = tk.Tk()
    app = AgentGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == '__main__':
    main()
