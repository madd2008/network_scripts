# version 4.5
#requirements 
# pip3 install scapy

import argparse
from scapy.all import sniff
import ipaddress
import sys
import subprocess

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Capture and process Win0 size TCP packets.')
parser.add_argument('-i', '--interface', metavar='interface', type=str, default='bond0', help='the interface to capture packets on')
parser.add_argument('-t', '--timeout', metavar='timeout', type=int, default=300, help='the timeout for capturing packets (default 360 seconds)')
parser.add_argument('-p', '--ping', metavar='ping', type=str, help='should we run ping tests after initial collection is done?)')
args = parser.parse_args()

# Define the RFC1918 private address space
private_nets = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
]

# Initialize a dictionary to store packets with the same source and destination IPs
packets_by_src_dst = {}

# Initialize a dictionary to store the IP addresses and their counts
ip_counts = {}

# Starting the packet capture
print("\nStarting the packet capture. Please wait " + str(args.timeout) + " seconds")
capture = sniff(iface=args.interface, filter='tcp[14:2]=0', timeout=args.timeout)

for packet in capture:
    if 'IP' in packet:
        src_ip = packet['IP'].src
        dst_ip = packet['IP'].dst
        if 'TCP' in packet:
            src_port = packet['TCP'].sport
            dst_port = packet['TCP'].dport

        # Count the number of times each IP address appears
        if src_ip in ip_counts:
            ip_counts[src_ip] += 1
        else:
            ip_counts[src_ip] = 1

        if dst_ip in ip_counts:
            ip_counts[dst_ip] += 1
        else:
            ip_counts[dst_ip] = 1

        # Keep track of packets with the same source and destination IPs
        src_dst_key = (src_ip, dst_ip)
        if src_dst_key in packets_by_src_dst:
            packets_by_src_dst[src_dst_key] += 1
        else:
            packets_by_src_dst[src_dst_key] = 1

# Sort the IP addresses based on the number of hits in descending order
sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)

if not sorted_ips:
    print('\nNo  issues identified')
    sys.exit()
else:
    # Initialize lists to hold the RFC1918 IPs and non-RFC1918 IPs
    rfc1918_ips = []
    other_ips = []

    # Separate the IPs based on whether they are in the RFC1918 private address space or not
    for ip, count in sorted_ips:
        if any(ipaddress.ip_address(ip) in private_net for private_net in private_nets):
            if count > int(args.timeout):
                rfc1918_ips.append((ip, count))
            # else:
            #     print('\nIgnoring IPs with insignificant number of ZeroWindow packets: ', ip, count)
        else:
            if count > int(args.timeout):
                other_ips.append((ip, count))
            # else:
            #     print('\nIgnoring IPs with insignificant number of ZeroWindow packets: ', ip, count)

    # Print out the sorted IP addresses and their counts
    print('\nPublic IP addresses with communication issues:')
    for ip, count in other_ips:
        print(ip + ": ZeroWindow packets: " + str(count) + "  PPS: " + str(int(count / args.timeout)))

    print('\nLocal IPs with internal communication issues:')
    for ip, count in rfc1918_ips:
        print(ip + ": ZeroWindow packets: " + str(count) + "  PPS: " + str(int(count / args.timeout)))

# Print out the source and destination IPs with the number of times they appear, sorted by packet count
print("\nThe problematic Source/ Destination pairs")
for (src_ip, dst_ip), packets in sorted(packets_by_src_dst.items(), key=lambda x: x[1], reverse=True):
    if packets > int(args.timeout / 2):
        print(f"Source IP: {src_ip}:{src_port}, Destination IP: {dst_ip}:{dst_port}, Count: {packets}")

if args.ping:
    if not rfc1918_ips:
        print("Tests concluded")
    else:
        for ip, count in rfc1918_ips:
            print("\nPinging with Jumbo packets", "\n Response time:")
            subprocess.call(['ping', '-c', '5', '-s', '8972', ip])
