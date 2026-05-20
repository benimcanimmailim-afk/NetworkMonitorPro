import webview
import threading
import time
import os
import re
import json
import ipaddress
import webbrowser
import multiprocessing
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import network_utils
from config_manager import ConfigManager

class Api:
    def __init__(self):
        self.config_mgr = ConfigManager()
        self.devices = [] # List of dicts: {ip, tag, status, latency, uptime, active}
        self.window = None
        self.ping_threads = {}

    def set_window(self, window):
        self.window = window

    def get_devices(self):
        return [{"ip": d["ip"], "tag": d["tag"], "status": d["status"],
                 "latency": d["latency"], "uptime": d["uptime"]} for d in self.devices]

    def get_packages(self):
        return self.config_mgr.load_all_packages()

    def bulk_add(self, text):
        ip_list = [ip for ip in re.split(r'[,\s\n]+', text.strip()) if ip]
        for ip in ip_list:
            self._add_device(ip)
        return True

    def _add_device(self, ip, tag=""):
        if any(d["ip"] == ip for d in self.devices):
            return

        device = {
            "ip": ip,
            "tag": tag,
            "status": "offline",
            "latency": "--",
            "uptime": 0,
            "active": True,
            "last_status": None
        }
        self.devices.append(device)
        thread = threading.Thread(target=self._ping_loop, args=(device,), daemon=True)
        thread.start()
        self.ping_threads[ip] = thread

    def _ping_loop(self, device):
        while device["active"]:
            ip = device["ip"]
            success, latency = network_utils.ping_ip(ip)

            if not device["active"]: break

            status = "online" if success else "offline"
            if success:
                device["uptime"] += 2
                device["latency"] = latency
            else:
                device["latency"] = "Hata"

            device["status"] = status

            # Push update to UI
            if self.window:
                ip_j = json.dumps(ip)
                status_j = json.dumps(status)
                latency_j = json.dumps(device['latency'])
                uptime_j = json.dumps(device['uptime'])
                self.window.evaluate_js(f"updateDeviceStatus({ip_j}, {status_j}, {latency_j}, {uptime_j})")

            time.sleep(2)

    def reset_devices(self):
        for d in self.devices:
            d["active"] = False
        self.devices = []
        self.ping_threads = {}
        return True

    def delete_device(self, ip):
        for d in self.devices:
            if d["ip"] == ip:
                d["active"] = False
                self.devices.remove(d)
                break
        return True

    def save_package(self, name):
        package_data = [{"ip": d["ip"], "tag": d["tag"]} for d in self.devices]
        self.config_mgr.save_package(name, package_data)
        return True

    def load_package(self, name):
        self.reset_devices()
        packages = self.config_mgr.load_all_packages()
        package_content = packages.get(name, [])
        for item in package_content:
            if isinstance(item, str):
                self._add_device(item)
            else:
                self._add_device(item.get("ip"), item.get("tag"))
        return True

    def delete_package(self, name):
        return self.config_mgr.delete_package(name)

    def manage_tag(self, ip, tag):
        for d in self.devices:
            if d["ip"] == ip:
                d["tag"] = tag
                if self.window:
                    ip_j = json.dumps(ip)
                    tag_j = json.dumps(tag)
                    self.window.evaluate_js(f"updateDeviceTag({ip_j}, {tag_j})")
                break
        return True

    def find_hostname(self, ip):
        def resolve():
            hostname = network_utils.resolve_hostname(ip)
            if hostname:
                self.manage_tag(ip, hostname)
        threading.Thread(target=resolve, daemon=True).start()
        return True

    def find_manufacturer(self, ip):
        def resolve():
            mfr = network_utils.get_manufacturer_from_arp(ip)
            if mfr:
                for d in self.devices:
                    if d["ip"] == ip:
                        new_tag = f"{d['tag']} ({mfr})" if d["tag"] else f"({mfr})"
                        self.manage_tag(ip, new_tag)
                        break
        threading.Thread(target=resolve, daemon=True).start()
        return True

    def open_web_ui(self, ip):
        is_443, is_80 = network_utils.check_web_ports(ip)
        if is_443: webbrowser.open(f"https://{ip}")
        elif is_80: webbrowser.open(f"http://{ip}")
        return True

    def connect_remote(self, protocol, ip):
        if protocol == 'ssh':
            network_utils.start_ssh(ip)
        elif protocol == 'rdp':
            network_utils.start_rdp(ip)
        return True

    def start_discovery(self, start_ip_str, end_ip_str):
        def scan_thread():
            try:
                start_ip = ipaddress.IPv4Address(start_ip_str.strip())
                end_ip = ipaddress.IPv4Address(end_ip_str.strip())
                ips = [str(ipaddress.IPv4Address(i)) for i in range(int(start_ip), int(end_ip) + 1)]
            except:
                return

            live_ips = []
            total = len(ips)
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(network_utils.fast_ping, ip): ip for ip in ips}
                for i, future in enumerate(futures):
                    ip = futures[future]
                    if future.result():
                        live_ips.append(ip)
                    if self.window:
                        self.window.evaluate_js(f"updateScanProgress({i+1}, {total})")

            if live_ips:
                # In this simplified version, discovery replaces current devices
                self.reset_devices()
                for ip in live_ips:
                    self._add_device(ip)

            if self.window:
                self.window.evaluate_js(f"updateScanProgress({total}, {total})")

        threading.Thread(target=scan_thread, daemon=True).start()
        return True

    def start_port_scan(self, ip):
        def run():
            results = network_utils.scan_ports(ip)
            res_str = "\n".join([f"Port {p}: {'OPEN' if s else 'CLOSED'}" for p, s in results])
            if self.window:
                msg = json.dumps(f"Port Scan Results for {ip}:\n{res_str}")
                self.window.evaluate_js(f"alert({msg})")
        threading.Thread(target=run, daemon=True).start()
        return True

    def start_traceroute(self, ip):
        def run():
            import subprocess
            import shutil
            if os.name == 'nt':
                cmd = ["tracert", "-d", ip]
                kwargs = {"creationflags": 0x08000000}
            else:
                if shutil.which("traceroute"):
                    cmd = ["traceroute", "-n", ip]
                else:
                    if self.window: self.window.evaluate_js("alert('traceroute not found')")
                    return
                kwargs = {}

            try:
                res = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
                if self.window:
                    msg = json.dumps(f"Traceroute to {ip}:\n{res.stdout}")
                    self.window.evaluate_js(f"alert({msg})")
            except Exception as e:
                if self.window:
                    msg = json.dumps(f"Error: {str(e)}")
                    self.window.evaluate_js(f"alert({msg})")
        threading.Thread(target=run, daemon=True).start()
        return True

if __name__ == "__main__":
    multiprocessing.freeze_support()
    api = Api()
    window = webview.create_window('Ultra Network Monitor V5 - NOC Edition', 'ui/index.html', js_api=api, width=1280, height=800)
    api.set_window(window)
    webview.start(debug=True)
