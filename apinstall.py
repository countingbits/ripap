#!/usr/bin/env python3
import argparse
import subprocess
import sys
import datetime
import shutil
from pathlib import Path

# Log file path
log_file_path = "setup.log"

# Parse command-line arguments for optional debug mode
def parse_arguments():
    parser = argparse.ArgumentParser(description="Setup script for Raspberry Pi access point and Pi-hole, with added backup and debug features.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for more verbose output.")
    return parser.parse_args()

args = parse_arguments()
debug_mode = args.debug

def log_message(message, level="INFO"):
    """Log a message to the setup.log file with a timestamp, and optionally print to console."""
    log_entry = f"{datetime.datetime.now()}: [{level}] {message}\n"
    with open(log_file_path, "a") as log_file:
        log_file.write(log_entry)
    if level in ["INFO", "ERROR"] or debug_mode:
        print(message)

def run_command(command, success_message="", failure_message=""):
    """Run a shell command and log its output, with error handling."""
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        log_message(success_message or f"Successfully executed: {command}")
        if debug_mode:
            log_message(f"Output: {output}")
    except subprocess.CalledProcessError as e:
        log_message(failure_message or f"Error executing {command}: {e.output}", level="ERROR")
        return False
    return True

def check_internet_connection(retry_attempts=1, failure_callbacks=[]):
    """Check for an active internet connection before proceeding."""
    log_message("Checking internet connection...")
    for _ in range(retry_attempts):
        if run_command("ping -c 4 8.8.8.8", "Internet connection is active.", "No internet connection detected."):
            return True
    log_message("Internet connection check failed after retries.")
    for callback in failure_callbacks:
        callback()
    return False

def diagnose_connection_issue():
    """Diagnose internet connection issue."""
    log_message("Diagnosing internet connection issue...")
    run_command("ip addr show", "Network interfaces:", "Failed to retrieve network interfaces.")

def install_python3():
    """Ensure Python 3 is installed on the Raspberry Pi."""
    log_message("Installing Python 3...")
    if not run_command("apt-get install -y python3 python3-pip", "Python 3 installed successfully.", "Failed to install Python 3."):
        sys.exit(1)

def ensure_ipv4_forwarding():
    """Enable IPv4 packet forwarding to allow the Pi to route traffic."""
    log_message("Enabling IPv4 forwarding...")
    if not run_command("sysctl -w net.ipv4.ip_forward=1", "IPv4 forwarding enabled.", "Failed to enable IPv4 forwarding."):
        sys.exit(1)
    run_command("sed -i '/net.ipv4.ip_forward=1/s/^#//g' /etc/sysctl.conf", "Made IPv4 forwarding persistent.")

def setup_nat_routing():
    """Set up NAT routing to allow connected devices to access the internet through the Pi."""
    log_message("Configuring NAT routing...")
    if not run_command("iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE", "NAT routing configured.", "Failed to configure NAT routing."):
        sys.exit(1)
    run_command("sh -c 'iptables-save > /etc/iptables.ipv4.nat'", "Saved iptables rule.")

def backup_file(file_path, backup_dir="/backup"):
    """Backup a specified configuration file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir_path = Path(backup_dir) / timestamp
    backup_file_path = backup_dir_path / Path(file_path).name
    backup_dir_path.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy(file_path, backup_file_path)
        log_message(f"Backed up {file_path} to {backup_file_path}")
    except Exception as e:
        log_message(f"Failed to backup {file_path}: {e}", level="ERROR")
        sys.exit(1)

def prompt_for_ap_config():
    """Prompt the user for access point configuration details, such as SSID and password."""
    print("Please enter your access point configuration details.")
    ssid = input("SSID Name: ")
    password = input("Password (min 8 characters): ")
    while len(password) < 8:
        print("Password must be at least 8 characters.")
        password = input("Password: ")
    channel = input("Channel (1-11): ")
    return ssid, password, channel

def configure_hostapd(ssid, password, channel):
    """Configure the hostapd service with the user's specified settings."""
    log_message("Configuring hostapd...")
    hostapd_config = f"""
interface=wlan0
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
wpa=2
wpa_passphrase={password}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
    """
    try:
        with open("/etc/hostapd/hostapd.conf", "w") as f:
            f.write(hostapd_config)
        log_message("Hostapd configured successfully.")
        run_command("systemctl restart hostapd", "Restarted hostapd.", "Failed to restart hostapd.")
    except Exception as e:
        log_message(f"Failed to configure hostapd: {e}", level="ERROR")
        sys.exit(1)

def main():
    global debug_mode
    log_message("Starting Raspberry Pi setup...")
    check_internet_connection()
    install_python3()
    ensure_ipv4_forwarding()
    setup_nat_routing()
    
    # Backup original hostapd configuration file
    backup_file("/etc/hostapd/hostapd.conf")
    
    # Configure the access point
    ssid, password, channel = prompt_for_ap_config()
    configure_hostapd(ssid, password, channel)
    
    log_message("Setup process almost complete. Rechecking internet connection...")
    # Recheck internet connection with retry and failure callbacks
    failure_callbacks = [diagnose_connection_issue]
    if not check_internet_connection(retry_attempts=3, failure_callbacks=failure_callbacks):
        log_message("Final internet connection check failed. See previous logs for diagnostic info.")

    log_message("Raspberry Pi setup complete. Review setup.log for details.")

if __name__ == "__main__":
    main()
