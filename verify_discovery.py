import network_utils
import socket

def test_discovery():
    print("Testing Hostname Resolution...")
    # 127.0.0.1 usually resolves to localhost
    hostname = network_utils.resolve_hostname("127.0.0.1")
    print(f"127.0.0.1 resolved to: {hostname}")

    print("\nTesting Fast Ping...")
    is_up = network_utils.fast_ping("127.0.0.1")
    print(f"127.0.0.1 is up: {is_up}")
    assert is_up == True

if __name__ == "__main__":
    test_discovery()
