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

def install_iptables():
    try:
        run_command("sudo apt-get install iptables-persistent")
        run_command("sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE")
        run_command("sudo sh -c 'iptables-save > /etc/iptables.ipv4.nat'")
        run_command("sudo sed -i '/net.ipv4.ip_forward=1/s/^#//g' /etc/sysctl.conf")
        run_command("sudo sysctl -w net.ipv4.ip_forward=1")
    except Exception as e:
        log_message(f"Failed to install iptables-persistent: {e}", level="ERROR")
        sys.exit(1)
        
        
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

def update_system_and_install_packages():
    """Update the system and install required packages for the access point."""
    log_message("Updating system packages. This might take a while...")
    if not run_command("apt-get update && apt-get upgrade -y", "System updated successfully.", "Failed to update the system."):
        sys.exit(1)

    log_message("Installing hostapd and dnsmasq...")
    if not run_command("apt-get install -y hostapd dnsmasq", "hostapd and dnsmasq installed successfully.", "Failed to install hostapd and dnsmasq."):
        sys.exit(1)

    # Disable services to prevent them from starting automatically until they are fully configured
    run_command("systemctl stop hostapd", "hostapd service stopped.", "Failed to stop hostapd service.")
    run_command("systemctl stop dnsmasq", "dnsmasq service stopped.", "Failed to stop dnsmasq service.")
    run_command("systemctl disable hostapd", "hostapd service disabled.", "Failed to disable hostapd service.")
    run_command("systemctl disable dnsmasq", "dnsmasq service disabled.", "Failed to disable dnsmasq service.")


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
    hostapd_config = hostapd_config = (
    f"interface=wlan0\n"
    f"driver=nl80211\n"
    f"ssid={ssid}\n"
    f"hw_mode=g\n"
    f"channel={channel}\n"
    f"wpa=2\n"
    f"wpa_passphrase={password}\n"
    f"wpa_key_mgmt=WPA-PSK\n"
    f"rsn_pairwise=CCMP"
)
    try:
        with open("/etc/hostapd/hostapd.conf", "w") as f:
            f.write(hostapd_config)
        log_message("Hostapd configured successfully.")
        run_command("systemctl restart hostapd", "Restarted hostapd.", "Failed to restart hostapd.")
    except Exception as e:
        log_message(f"Failed to configure hostapd: {e}", level="ERROR")
        sys.exit(1)
        
def enable_and_start_services():
    """Enable and start required services for the access point."""
    log_message("Enabling and starting hostapd and dnsmasq services...")
    services = ["hostapd", "dnsmasq"]
    for service in services:
        if not run_command(f"systemctl enable {service}", f"{service} service enabled.", f"Failed to enable {service} service."):
            sys.exit(1)
        if not run_command(f"systemctl start {service}", f"{service} service started.", f"Failed to start {service} service."):
            sys.exit(1)

def prompt_for_reboot():
    """Prompt the user for a system reboot to apply changes."""
    reboot = input("Setup is complete. Would you like to reboot now? (yes/no): ")
    if reboot.lower() in ['yes', 'y']:
        log_message("Rebooting the system to apply changes...")
        run_command("reboot", "System is rebooting...", "Failed to initiate reboot.")
    else:
        log_message("Reboot skipped. Please manually reboot the system later to apply changes.")

def main():
    global debug_mode
    log_message("Starting Raspberry Pi setup...")
    install_iptables()
    check_internet_connection(retry_attempts=1, failure_callbacks=[diagnose_connection_issue])
    update_system_and_install_packages()
    ensure_ipv4_forwarding()
    setup_nat_routing()
    
   
    
    # Configure the access point
    ssid, password, channel = prompt_for_ap_config()
    configure_hostapd(ssid, password, channel)
    
     # Backup original hostapd configuration file
    #backup_file("/etc/hostapd/hostapd.conf")
    
    #enable services and reboot pi
    enable_and_start_services()
    
    
    log_message("Setup process almost complete. Rechecking internet connection...")
    # Recheck internet connection with retry and failure callbacks
    if not check_internet_connection(retry_attempts=3, failure_callbacks=[diagnose_connection_issue]):
        log_message("Final internet connection check failed. See previous logs for diagnostic info.")
        
    prompt_for_reboot()
    
    
    log_message("Raspberry Pi setup complete.")

if __name__ == "__main__":
    main()
