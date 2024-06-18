from scapy.all import *
import time
start_time = None
end_time = None


def packet_callback(packet):
    if packet.haslayer(TCP):
        if packet[TCP].dport == 443: # Puerto HTTPS
            if 'facebook.com' in packet[TCP].payload:
                print("Comunicación con Facebook detectada")


if __name__ == "__main__":
    print("Capturando paquetes de red...")
    sniff(prn=packet_callback, filter="ip")