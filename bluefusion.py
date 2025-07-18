#!/usr/bin/env python3
"""
BlueFusion - Dual BLE Interface Controller
Main entry point for the application
"""
import click
import subprocess
import sys
import os
import time
import signal
import psutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

processes = []

def kill_existing_services():
    """Kill any existing BlueFusion services on default ports"""
    ports_to_check = [8000, 7860]  # API and UI ports
    killed_pids = []
    
    for port in ports_to_check:
        try:
            # Find processes using the port
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check if process is using the port
                    for conn in proc.net_connections():
                        if conn.laddr.port == port and conn.status == 'LISTEN':
                            print(f"⚠️  Killing process using port {port} (PID: {proc.pid})")
                            proc.terminate()
                            killed_pids.append(proc.pid)
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                                proc.wait(timeout=2)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
        except Exception as e:
            print(f"Warning: Could not check port {port}: {e}")
    
    # Also kill any remaining python processes that might be BlueFusion related
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and any('fastapi_server.py' in str(arg) or 
                                     'gradio_interface.py' in str(arg) for arg in cmdline):
                        if proc.pid not in killed_pids:
                            print(f"⚠️  Killing remaining BlueFusion process (PID: {proc.pid})")
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                                proc.wait(timeout=2)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
    except Exception as e:
        print(f"Warning: Could not check for remaining processes: {e}")
    
    # Wait longer for processes to fully terminate and ports to be released
    time.sleep(2)

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\n\nShutting down BlueFusion...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """BlueFusion - AI-powered dual BLE interface controller"""
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='API host')
@click.option('--port', default=8000, help='API port')
def api(host, port):
    """Start the FastAPI server"""
    print(f"🔵 Starting BlueFusion API on http://{host}:{port}")
    cmd = [sys.executable, "src/api/fastapi_server.py"]
    
    # If not default, pass host/port to uvicorn
    if host != '0.0.0.0' or port != 8000:
        cmd = [sys.executable, "-m", "uvicorn", "src.api.fastapi_server:app", 
               f"--host={host}", f"--port={port}", "--reload"]
    
    subprocess.run(cmd)


@cli.command()
@click.option('--host', default='0.0.0.0', help='UI host')
@click.option('--port', default=7860, help='UI port')
@click.option('--share', is_flag=True, help='Create public Gradio link')
def ui(host, port, share):
    """Start the Gradio interface"""
    print(f"🎨 Starting BlueFusion UI on http://{host}:{port}")
    
    # Set environment variables for Gradio
    env = os.environ.copy()
    env['GRADIO_SERVER_NAME'] = host
    env['GRADIO_SERVER_PORT'] = str(port)
    if share:
        env['GRADIO_SHARE'] = 'true'
    
    subprocess.run([sys.executable, "src/ui/gradio_interface.py"], env=env)


@cli.command()
@click.option('--api-port', default=8000, help='API port')
@click.option('--ui-port', default=7860, help='UI port')
@click.option('--no-ui', is_flag=True, help='Start API only')
def start(api_port, ui_port, no_ui):
    """Start both API and UI servers"""
    global processes
    
    print("🔵 Starting BlueFusion...")
    
    # First, kill any existing services
    print("🧹 Checking for existing BlueFusion services...")
    kill_existing_services()
    
    # Start API
    print(f"\n1. Starting API server on http://localhost:{api_port}")
    api_cmd = [sys.executable, "src/api/fastapi_server.py"]
    if api_port != 8000:
        api_cmd = [sys.executable, "-m", "uvicorn", "src.api.fastapi_server:app", 
                   f"--port={api_port}", "--reload"]
    
    api_process = subprocess.Popen(api_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    processes.append(api_process)
    
    # Wait for API to start
    print("   Waiting for API to initialize...")
    time.sleep(3)
    
    if not no_ui:
        # Start UI
        print(f"\n2. Starting UI on http://localhost:{ui_port}")
        env = os.environ.copy()
        env['GRADIO_SERVER_PORT'] = str(ui_port)
        ui_process = subprocess.Popen(
            [sys.executable, "src/ui/gradio_interface.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env
        )
        processes.append(ui_process)
    
    print("\n✅ BlueFusion is running!")
    print(f"\n   API docs: http://localhost:{api_port}/docs")
    if not no_ui:
        print(f"   UI: http://localhost:{ui_port}")
    print("\nPress Ctrl+C to stop\n")
    
    # Monitor processes
    try:
        while True:
            time.sleep(1)
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    print(f"\nWarning: Process {i} has stopped!")
                    # Read some output
                    if p.stdout:
                        output = p.stdout.read(500).decode('utf-8', errors='ignore')
                        if output:
                            print(f"Last output: {output}")
    except KeyboardInterrupt:
        signal_handler(None, None)


@cli.command()
def scan():
    """Quick BLE scan using MacBook interface"""
    from interfaces.macbook_ble import MacBookBLE
    import asyncio
    
    async def quick_scan():
        print("🔍 Scanning for BLE devices (10 seconds)...\n")
        
        mac_ble = MacBookBLE()
        await mac_ble.initialize()
        
        devices_seen = set()
        
        def packet_callback(packet):
            if packet.address not in devices_seen:
                devices_seen.add(packet.address)
                name = packet.metadata.get('name', 'Unknown')
                print(f"Found: {packet.address} | {name:20} | RSSI: {packet.rssi} dBm")
        
        mac_ble.register_callback(packet_callback)
        
        await mac_ble.start_scanning()
        await asyncio.sleep(10)
        await mac_ble.stop_scanning()
        
        print(f"\n✅ Scan complete. Found {len(devices_seen)} unique devices.")
    
    asyncio.run(quick_scan())


@cli.command()
def test():
    """Run the test suite"""
    print("🧪 Running BlueFusion tests...")
    subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])


if __name__ == "__main__":
    cli()