import subprocess
import plistlib
import re

AIRPORT_PATH = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"

def scan_networks():
    """Scans for available Wi-Fi networks using macOS airport utility."""
    try:
        # Run airport scan
        result = subprocess.run([AIRPORT_PATH, "-s"], capture_output=True, text=True)
        if result.returncode != 0:
            return []

        networks = []
        # Skip header line
        lines = result.stdout.strip().split('\n')[1:]
        
        for line in lines:
            # Parse fixed width output: "SSID BSSID RSSI CHANNEL HT CC SECURITY"
            # This is a bit fragile, so regex is better
            # Sample: "MyWiFi aa:bb:cc:dd:ee:ff -50  1      Y  US WPA2(PSK/AES)"
            match = re.search(r'^\s*(.*?)\s+([0-9a-f:]{17})\s+([-0-9]+)\s+([0-9,+]+)\s', line)
            if match:
                ssid = match.group(1).strip()
                if ssid: # Filter empty SSIDs
                    networks.append({
                        'ssid': ssid,
                        'bssid': match.group(2),
                        'rssi': int(match.group(3)),
                        'channel': match.group(4)
                    })
        
        # Deduplicate by SSID, keeping strongest signal
        unique_networks = {}
        for net in networks:
            ssid = net['ssid']
            if ssid not in unique_networks or net['rssi'] > unique_networks[ssid]['rssi']:
                unique_networks[ssid] = net
                
        return sorted(list(unique_networks.values()), key=lambda x: x['rssi'], reverse=True)
    except Exception as e:
        print(f"Error scanning wifi: {e}")
        return []

def connect_network(ssid, password):
    """Connects to a Wi-Fi network using networksetup."""
    # Note: Requires correct device name. Usually en0 for wifi on modern macs.
    # We can detect it.
    device = "en0" # Default assumption
    
    # Try to find wifi device
    try:
        dev_out = subprocess.run(["networksetup", "-listallhardwareports"], capture_output=True, text=True).stdout
        # Basic parsing looking for "Wi-Fi" then reading next line for Device: enX
        lines = dev_out.split('\n')
        for i, line in enumerate(lines):
            if "Wi-Fi" in line:
                if i+1 < len(lines) and "Device: " in lines[i+1]:
                    device = lines[i+1].split(": ")[1].strip()
                    break
    except:
        pass

    try:
        cmd = ["networksetup", "-setairportnetwork", device, ssid, password]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, "Connected successfully"
        else:
            return False, f"Connection failed: {result.stderr}"
    except Exception as e:
        return False, str(e)
