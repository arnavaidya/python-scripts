import subprocess
import sys
from pathlib import Path

def read_subdomains_from_file(file_path):
    """Read subdomains from a text file, one per line"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # Read lines, strip whitespace, and filter out empty lines
            subdomains = [line.strip() for line in file if line.strip()]
        return subdomains
    except FileNotFoundError:
        print(f"[!] Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"[!] Error reading file '{file_path}': {e}")
        return []

def check_subdomain_status(subdomains, use_https=True, timeout=10):
    """Check HTTP status of subdomains and return those with success/redirect status codes"""
    live_subdomains = []
    protocol = 'https' if use_https else 'http'
    
    # Define success status codes to check for
    success_codes = ['200', '301', '302', '308']
    
    print(f"Checking {len(subdomains)} subdomains with {protocol.upper()}...")
    print("Looking for status codes: 200 (OK), 301 (Moved Permanently), 302 (Found), 308 (Permanent Redirect)")
    print("-" * 100)
    
    for i, subdomain in enumerate(subdomains, 1):
        # Remove protocol if already present in subdomain
        clean_subdomain = subdomain.replace('http://', '').replace('https://', '')
        url = f"{protocol}://{clean_subdomain}"
        
        try:
            # Using curl to fetch only the status code
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--connect-timeout", str(timeout), url],
                capture_output=True, text=True, timeout=timeout + 5
            )
            
            status_code = result.stdout.strip()
            
            if status_code in success_codes:
                status_description = {
                    '200': 'OK',
                    '301': 'Moved Permanently',
                    '302': 'Found',
                    '308': 'Permanent Redirect'
                }.get(status_code, 'Unknown')
                
                print(f"[{i:3d}] [+] {status_code} {status_description}: {url}")
                live_subdomains.append((clean_subdomain, status_code, status_description))
            else:
                print(f"[{i:3d}] [-] {status_code}: {url}")
                
        except subprocess.TimeoutExpired:
            print(f"[{i:3d}] [!] Timeout: {url}")
        except Exception as e:
            print(f"[{i:3d}] [!] Error checking {url}: {e}")
    
    return live_subdomains

def print_results_table(live_subdomains, use_https=True):
    """Print results in a formatted table"""
    if not live_subdomains:
        return
    
    protocol = 'https' if use_https else 'http'
    
    # Calculate column widths
    max_url_length = max(len(f"{protocol}://{subdomain}") for subdomain, _, _ in live_subdomains)
    max_url_length = max(max_url_length, len("URL"))
    max_desc_length = max(len(status_description) for _, _, status_description in live_subdomains)
    max_desc_length = max(max_desc_length, len("Description"))
    
    # Table formatting
    url_width = max_url_length + 2
    code_width = 6  # "Code" + padding
    desc_width = max_desc_length + 2
    
    # Print table header
    print(f"┌{'─' * url_width}┬{'─' * code_width}┬{'─' * desc_width}┐")
    print(f"│ {'URL':<{url_width-1}}│ {'Code':<{code_width-1}}│ {'Description':<{desc_width-1}}│")
    print(f"├{'─' * url_width}┼{'─' * code_width}┼{'─' * desc_width}┤")
    
    # Print table rows
    for subdomain, status_code, status_description in live_subdomains:
        url = f"{protocol}://{subdomain}"
        print(f"│ {url:<{url_width-1}}│ {status_code:<{code_width-1}}│ {status_description:<{desc_width-1}}│")
    
    # Print table footer
    print(f"└{'─' * url_width}┴{'─' * code_width}┴{'─' * desc_width}┘")

def save_results_to_file(live_subdomains, output_file="live_subdomains.txt", use_https=True):
    """Save live subdomains to output file with status codes"""
    try:
        protocol = 'https' if use_https else 'http'
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write("# Live Subdomains with Status Codes\n")
            file.write("-" * 100 + "\n")
            
            if live_subdomains:
                # Calculate column widths for file output
                max_url_length = max(len(f"{protocol}://{subdomain}") for subdomain, _, _ in live_subdomains)
                max_url_length = max(max_url_length, len("URL"))
                max_desc_length = max(len(status_description) for _, _, status_description in live_subdomains)
                max_desc_length = max(max_desc_length, len("Description"))
                
                url_width = max_url_length + 2
                code_width = 6
                desc_width = max_desc_length + 2
                
                # Write table header to file
                file.write(f"┌{'─' * url_width}┬{'─' * code_width}┬{'─' * desc_width}┐\n")
                file.write(f"│ {'URL':<{url_width-1}}│ {'Code':<{code_width-1}}│ {'Description':<{desc_width-1}}│\n")
                file.write(f"├{'─' * url_width}┼{'─' * code_width}┼{'─' * desc_width}┤\n")
                
                # Write table rows to file
                for subdomain, status_code, status_description in live_subdomains:
                    url = f"{protocol}://{subdomain}"
                    file.write(f"│ {url:<{url_width-1}}│ {status_code:<{code_width-1}}│ {status_description:<{desc_width-1}}│\n")
                
                # Write table footer to file
                file.write(f"└{'─' * url_width}┴{'─' * code_width}┴{'─' * desc_width}┘\n")
            
        print(f"\n[+] Results saved to '{output_file}'")
    except Exception as e:
        print(f"[!] Error saving to file: {e}")

def print_banner():
    """Print the ASCII banner"""
    print(r""" ____        _     _ _           
/ ___| _   _| |__ | | |_   _____ 
\___ \| | | | '_ \| | \ \ / / _ \
 ___) | |_| | |_) | |_|\ V /  __/
|____/ \__,_|_.__/|_(_) \_/ \___|""")
    print("\nSubLive - Subdomain Status Checker")
    print("Status codes checked: 200 (OK), 301 (Moved Permanently), 302 (Found), 308 (Permanent Redirect)")
    print("\n# Coded By Arnav Vaidya - @arnavaidya")
    print("=" * 100)

def main():
    # Always print banner first
    print_banner()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python sublive.py <subdomains_file.txt> [options]")
        print("\nOptions:")
        print("  --http          Use HTTP instead of HTTPS")
        print("  --timeout <n>   Set timeout in seconds (default: 10)")
        print("  --output <file> Save results to file (default: live_subdomains.txt)")
        print("\nStatus codes checked: 200 (OK), 301 (Moved Permanently), 302 (Found), 308 (Permanent Redirect)")
        print("\nExample:")
        print("  python sublive.py subdomains.txt")
        print("  python sublive.py subdomains.txt --http --timeout 15")
        return
    
    # Parse command line arguments
    input_file = sys.argv[1]
    use_https = True
    timeout = 10
    output_file = "live_subdomains.txt"
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--http":
            use_https = False
        elif sys.argv[i] == "--timeout" and i + 1 < len(sys.argv):
            try:
                timeout = int(sys.argv[i + 1])
                i += 1
            except ValueError:
                print("[!] Invalid timeout value. Using default (10 seconds).")
        elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 1
        i += 1
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"[!] Error: File '{input_file}' does not exist.")
        return
    
    # Read subdomains from file
    print(f"\nReading subdomains from '{input_file}'...")
    subdomains = read_subdomains_from_file(input_file)
    
    if not subdomains:
        print("[!] No valid subdomains found in the file.")
        return
    
    # Check subdomain status
    live_subdomains = check_subdomain_status(subdomains, use_https, timeout)
    
    # Display results
    print("\n" + "=" * 100)
    print(f"RESULTS: Found {len(live_subdomains)} live subdomains with valid status codes:")
    print("=" * 100)
    
    if live_subdomains:
        print_results_table(live_subdomains, use_https)
        
        # Save results to file
        save_results_to_file(live_subdomains, output_file, use_https)
    else:
        print("No live subdomains found.")

if __name__ == "__main__":
    main()