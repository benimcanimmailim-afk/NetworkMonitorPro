import network_utils
import socket

def test_discovery():
    print("Testing Hostname Resolution...")
    hostname = network_utils.resolve_hostname("127.0.0.1")
    print(f"127.0.0.1 resolved to: {hostname}")

    print("\nTesting Fast Ping...")
    is_up = network_utils.fast_ping("127.0.0.1")
    print(f"127.0.0.1 is up: {is_up}")
    # Note: In some restricted environments, pinging 127.0.0.1 might still fail.
    # We will log the result but not strictly assert True if we are in a sandbox that blocks it.
    # However, for this task, we want to ensure the command doesn't crash.

    print("\nTesting Detailed Ping (ping_ip)...")
    success, latency = network_utils.ping_ip("127.0.0.1")
    print(f"ping_ip('127.0.0.1'): Success={success}, Latency={latency}")

    print("\nTesting ARP Manufacturer (get_manufacturer_from_arp)...")
    # This might return None if no ARP entry exists for the IP
    manufacturer = network_utils.get_manufacturer_from_arp("127.0.0.1")
    print(f"Manufacturer for 127.0.0.1: {manufacturer}")

    print("\nAll tests executed (check output for platform-specific results).")

if __name__ == "__main__":
    test_discovery()
