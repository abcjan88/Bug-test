import subprocess
import requests
import socket
import dns.resolver
import os
import time
import sys

# กำหนดพอร์ตมาตรฐานที่ต้องการตรวจสอบ
standard_ports = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    21: "FTP",
    25: "SMTP",
    110: "POP3",
    53: "DNS",
    853: "DNS over TLS"
}

cloudflare_dns_ips = {"1.1.1.1", "1.0.0.1"}

def print_banner():
    banner = """
     
██╗  ██╗████████╗████████╗ ██████╗  ██████╗ ██╗     
██║ ██╔╝╚══██╔══╝╚══██╔══╝██╔═══██╗██╔═══██╗██║     
█████╔╝    ██║█████╗██║   ██║   ██║██║   ██║██║     
██╔═██╗    ██║╚════╝██║   ██║   ██║██║   ██║██║     
██║  ██╗   ██║      ██║   ╚██████╔╝╚██████╔╝███████╗
╚═╝  ╚═╝   ╚═╝      ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
   KT-TOOL  Rev0.0000000001                                              

    """
    print(banner)

def get_host():
    host = input("Enter the host you want to check (or type 'exit' to return):\nYou Host: ")  # ให้ prompt ลงมาที่บรรทัดใหม่
    if host.lower() == "exit":
        return None  # ถ้าพิมพ์ exit จะส่งค่า None กลับ
    return host

def test_connectivity(host):
    try:
        response = requests.get(f"http://{host}", timeout=5)
        if response.status_code:
            print("\033[1;32m\033[1mConnection Status: Connection Successful\033[0m")  # ตัวอักษรหนาสีเขียว
            return True
    except requests.exceptions.RequestException:
        print("Connection Status: Connection Failed")
        return False

def check_dnssec(host):
    try:
        result = subprocess.run(['nslookup', '-type=DNSKEY', host], capture_output=True, text=True)
        if 'DNSKEY' in result.stdout:
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred during DNSSEC check: {e}")
        return False

def check_http_status(host):
    try:
        response = requests.get(f"http://{host}", timeout=5)
        return response.status_code
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during HTTP check: {e}")
        return None

def check_open_ports(host):
    print("\nPort Status:")
    for port, service in standard_ports.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)  # ตั้งเวลา Timeout
            result = sock.connect_ex((host, port))
            if result == 0:
                print(f"\033[1;32mPort {port} ({service}): OPEN\033[0m")  # สีเขียวเมื่อเปิด
            else:
                print(f"\033[1;31mPort {port} ({service}): CLOSED\033[0m")  # สีแดงเมื่อปิด

def check_cloudflare_dns(host):
    try:
        resolver = dns.resolver.Resolver()
        answers = resolver.resolve(host, 'A')
        for answer in answers:
            if answer.to_text() in cloudflare_dns_ips:
                print("\033[1;32mCloudflare DNS: Using Cloudflare DNS\033[0m")  # สีเขียวหากใช้ Cloudflare DNS
                return
        print("\033[1;31mCloudflare DNS: Not using Cloudflare DNS\033[0m")  # สีแดงหากไม่ใช้ Cloudflare DNS
    except Exception as e:
        print(f"An error occurred during Cloudflare DNS check: {e}")

def print_result(dnssec_enabled, http_status):
    if dnssec_enabled:
        print("\033[1;31mDNSSEC KEY IS OPEN\033[0m")
    else:
        print("\033[1;32mDNSSEC KEY IS OFF\033[0m")
    
    if http_status is not None:
        if http_status == 200:
            print("HTTP Status: 200 OK")
        elif http_status == 403:
            print("HTTP Status: 403 Forbidden")
        elif http_status == 301:
            print("HTTP Status: 301 Moved Permanently")
        else:
            print(f"HTTP Status: {http_status}")

def loading_bar(duration):
    total = 20
    for i in range(total):
        percent = (i + 1) / total
        bar = '#' * (i + 1) + '-' * (total - i - 1)
        sys.stdout.write(f'\r[{bar}] {percent:.0%}')
        sys.stdout.flush()
        time.sleep(duration / total)
    sys.stdout.write('\r[####################] 100%\n')

def loading_animation(duration):
    print("Exiting", end="")
    for _ in range(duration):
        time.sleep(1)
        print(".", end="")
        sys.stdout.flush()
    print()  # สำหรับขึ้นบรรทัดใหม่หลังจากเสร็จ

def scan_host():
    while True:
        host = get_host()
        if host is None:  # ถ้าผู้ใช้พิมพ์ 'exit'
            return  # กลับไปยังเมนูหลัก
        print("Preparing to scan...")
        loading_bar(5)  # แสดงแอนิเมชันโหลดก่อนการสแกน
        time.sleep(2)  # หน่วงเวลา 2 วินาทีก่อนเริ่มการสแกน

        if test_connectivity(host):
            dnssec_enabled = check_dnssec(host)
            time.sleep(2)  # หน่วงเวลาก่อนแสดงผลการสแกน
            http_status = check_http_status(host)
            print_result(dnssec_enabled, http_status)
            check_open_ports(host)
            check_cloudflare_dns(host)
        
        input("Press Enter to scan other hosts ...")  # ให้กด Enter เพื่อกลับเมนูหลัก

def nmap_scan():
    host = input("Enter the host to scan for SNI BUG: ")
    print(f"Scanning {host} for SNI...")
    try:
        os.system(f"nmap --script ssl-enum-ciphers -p 443 {host}")  # เปลี่ยนพอร์ตตามต้องการ
    except Exception as e:
        print(f"An error occurred during Nmap scan: {e}")

    input("Press Enter to return to the main menu...")  # ให้กด Enter เพื่อกลับเมนูหลัก

def main_menu():
    while True:
        print("\n1. Scan Host For BUG")
        print("2. Nmap for SNI BUG")
        print("3. Exit")
        choice = input("Select an option: ")

        if choice == "1":
            scan_host()
            print_banner()  # เรียกแบนเนอร์หลังจากสแกนเสร็จ
        elif choice == "2":
            nmap_scan()
            print_banner()  # เรียกแบนเนอร์หลังจากสแกนเสร็จ
        elif choice == "3":
            loading_animation(3)  # เรียกใช้แอนิเมชันหน่วงเวลา 3 วินาที
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    print_banner()
    main_menu()
