import subprocess
import re
import time

print(r"""            
   / \   _ __ _ __   __ ___   __ \ \   / /_ _(_) __| |_   _  __ _ 
  / _ \ | '__| '_ \ / _` \ \ / /  \ \ / / _` | |/ _` | | | |/ _` |
 / ___ \| |  | | | | (_| |\ V /    \ V / (_| | | (_| | |_| | (_| |
/_/   \_\_|  |_| |_|\__,_| \_/      \_/ \__,_|_|\__,_|\__, |\__,_|
                                                      |___/        """)
print("\n****************************************************************")
print("\n* Copyright of Arnav Vaidya, 2025                              *")
print("\n****************************************************************")

# Function to scan and display Wi-Fi networks using Windows netsh command
def scan_wifi():
    try:
        # Run the command to display networks before scanning
        subprocess.run("netsh wlan show networks mode=bssid", shell=True, text=True, errors="ignore")

        # Run the command to capture the output
        output = subprocess.check_output("netsh wlan show networks mode=bssid", shell=True, text=True, errors="ignore")

        networks = []
        current_ssid = None
        bssid = None  # Initialize bssid to avoid UnboundLocalError

        for line in output.split("\n"):
            line = line.strip()

            if line.startswith("SSID"):
                ssid_match = re.search(r"SSID\s\d+\s:\s(.+)", line)
                current_ssid = ssid_match.group(1) if ssid_match else "Unknown"

            elif line.startswith("BSSID"):
                bssid_match = re.search(r"BSSID\s\d+\s:\s([0-9A-Fa-f:-]+)", line)
                bssid = bssid_match.group(1) if bssid_match else "Unknown"

            elif "Signal" in line:
                signal_match = re.search(r"Signal\s:\s(\d+)%", line)
                signal = int(signal_match.group(1)) if signal_match else 0

            elif "Authentication" in line:
                security_match = re.search(r"Authentication\s:\s(.+)", line)
                security = security_match.group(1) if security_match else "Unknown"

                if current_ssid and bssid:  # Ensure both values exist before appending
                    networks.append({"SSID": current_ssid, "BSSID": bssid, "Signal": signal, "Security": security})
                
                # Reset bssid after each network entry to prevent carrying over incorrect values
                bssid = None  

        return networks

    except subprocess.CalledProcessError as e:
        print(f"Error scanning Wi-Fi: {e}")
        return []

# Main Execution
if __name__ == "__main__":
    try:
        while True:
            print("\n--- Running Wi-Fi Scan ---")
            wifi_networks = scan_wifi()

            #if wifi_networks:
                #print("\n--- Wi-Fi Scan Results ---")
                #for net in wifi_networks:
                   #print(f"SSID: {net['SSID']} | BSSID: {net['BSSID']} | Signal: {net['Signal']}% | Security: {net['Security']}")
                   
            #else:
                #print("No networks found.")

            if not wifi_networks:
                print("No networks found.")

            time.sleep(10)  # Scan every 10 seconds

    except KeyboardInterrupt:
        print("\nScript terminated by user.")