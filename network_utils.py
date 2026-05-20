import subprocess
import re
import os
import socket
from concurrent.futures import ThreadPoolExecutor

CREATE_NO_WINDOW = 0x08000000

def scan_ports(ip):
    critical_ports = [21, 22, 23, 80, 443, 445, 1433, 3306, 3389, 5432, 8080, 27017, 6379]
    results = []

    def check_port(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                res = s.connect_ex((ip, port))
                return (port, res == 0)
        except:
            return (port, False)

    with ThreadPoolExecutor(max_workers=13) as executor:
        results = list(executor.map(check_port, critical_ports))

    return sorted(results)

def resolve_hostname(ip):
    try:
        # socket.gethostbyaddr returns (hostname, aliaslist, ipaddrlist)
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except (socket.herror, socket.gaierror, socket.timeout):
        return None

def fast_ping(ip):
    try:
        if os.name == 'nt':
            args = ["ping", "-n", "1", "-w", "200", ip]
            kwargs = {"creationflags": CREATE_NO_WINDOW}
        else:
            args = ["ping", "-c", "1", "-W", "1", ip]
            kwargs = {}
        res = subprocess.run(args, capture_output=True, text=True, shell=False, **kwargs)
        return res.returncode == 0
    except:
        return False

def check_web_ports(ip):
    # Returns (is_443_open, is_80_open)
    results = {}
    for port in [443, 80]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                res = s.connect_ex((ip, port))
                results[port] = (res == 0)
        except:
            results[port] = False
    return results[443], results[80]

def get_manufacturer_from_arp(ip):
    try:
        if os.name == 'nt':
            args = ["arp", "-a", ip]
            kwargs = {"shell": True}
        else:
            args = ["arp", "-n", ip]
            kwargs = {"shell": False}
        res = subprocess.run(args, capture_output=True, text=True, **kwargs)
        mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", res.stdout)
        if mac_match:
            mac = mac_match.group(0).replace("-", ":").upper()
            oui = mac[:8]

            oui_dict = {
                # Infrastructure & Network
                "00:00:0C": "Cisco", "00:01:42": "Cisco", "00:03:6B": "Cisco",
                "00:04:4D": "Cisco", "00:27:0D": "Cisco", "00:1A:11": "Cisco",
                "00:13:C3": "Cisco", "00:10:DB": "Juniper", "00:18:82": "Huawei",
                "70:79:B3": "Huawei", "00:1E:10": "Huawei", "E4:A8:B6": "Huawei",
                "3C:D9:2B": "HP/Aruba", "00:0F:20": "HP/Aruba", "4C:5E:0C": "Mikrotik",
                "64:D1:54": "Mikrotik", "78:8A:20": "Ubiquiti", "24:A4:3C": "Ubiquiti",
                "00:09:0F": "Fortinet", "00:1B:17": "Palo Alto", "50:3E:AA": "TP-Link",
                "1C:7E:E5": "D-Link",
                # Servers & Virtualization
                "00:50:56": "VMware", "00:0C:29": "VMware", "00:05:69": "VMware",
                "BC:30:5B": "Dell", "00:14:22": "Dell", "00:1D:09": "Dell",
                "00:17:A4": "HP Server", "00:13:72": "Intel", "00:03:FF": "Microsoft",
                "00:15:5D": "Hyper-V", "00:25:90": "Supermicro",
                # End Devices & Cameras
                "18:66:DA": "Apple", "00:17:F2": "Apple", "3C:37:86": "Apple",
                "00:17:C8": "Samsung", "00:40:3D": "Hikvision", "90:02:A9": "Dahua",
                "00:E0:4C": "Realtek", "28:D2:44": "Xiaomi",
                # Printers
                "00:00:85": "Canon", "00:1E:8F": "Canon", "00:00:48": "Epson",
                "00:18:71": "HP Printer", "D8:67:D9": "HP", "00:11:0A": "HP"
            }
            return oui_dict.get(oui, "Bilinmiyor")
        return None
    except:
        return None

def ping_ip(ip):
    try:
        if os.name == 'nt':
            args = ["ping", "-n", "1", "-w", "800", ip]
            kwargs = {"creationflags": CREATE_NO_WINDOW}
        else:
            args = ["ping", "-c", "1", "-W", "1", ip]
            kwargs = {}
        res = subprocess.run(args, capture_output=True, text=True, shell=False, **kwargs)
        if res.returncode == 0:
            if os.name == 'nt':
                match = re.search(r"(\d+)ms", res.stdout)
            else:
                match = re.search(r"time=(\d+\.?\d*)", res.stdout)
            return True, match.group(1) if match else "1"
        return False, "Hata"
    except:
        return False, "Hata"

def start_ssh(ip):
    # Basic IP validation to prevent command injection
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        return False, "Geçersiz IP adresi."

    if os.name == 'nt':
        try:
            # Safe execution using subprocess with arguments
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", f"ssh baykar@{ip}"], shell=False)
            return True, "SSH başlatılıyor..."
        except Exception as e:
            return False, f"SSH başlatılamadı: {str(e)}"
    else:
        return False, "SSH bu platformda otomatik olarak başlatılamıyor. Lütfen terminalden bağlamayı deneyin."

def start_rdp(ip):
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        return False, "Geçersiz IP adresi."

    if os.name == 'nt':
        try:
            subprocess.Popen(["cmd", "/c", "start", "mstsc", f"/v:{ip}"], shell=False)
            return True, "RDP başlatılıyor..."
        except Exception as e:
            return False, f"RDP başlatılamadı: {str(e)}"
    else:
        return False, "RDP bu platformda desteklenmiyor (Mstsc bulunamadı)."
