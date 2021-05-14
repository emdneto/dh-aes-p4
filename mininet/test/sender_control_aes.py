import scapy.all as scapy

input("Press Enter to continue...")
scapy.srp1(scapy.Ether(type=0x812)/("\x00"*33), timeout=0)
