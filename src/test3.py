from scapy.all import sniff, TCP, IP

import socket
import time

# Lista de dominios de Facebook para una detección más precisa
facebook_domains = ["facebook.com", "fbcdn.net", "fb.com", "fbsbx.com", "fbcdn.com"]

start_time = None
end_time = None

def packet_callback(packet):
    global start_time, end_time
    if TCP in packet and packet[TCP].dport == 443:
        # Intenta extraer el host del paquete IP
        try:
            ip_address = packet[IP].dst
            # Traduce la dirección IP a un nombre de dominio
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            # Busca si el nombre de dominio contiene alguno de los dominios de Facebook
            if any(domain in hostname for domain in facebook_domains):
                if start_time is None:
                    start_time = time.time()
                end_time = time.time()
                print("Se ha detectado una conexión a Facebook:", packet.summary())
        except socket.herror:
            # Maneja el caso en que la dirección IP no tenga un nombre de dominio asociado
            pass

if __name__ == "__main__":
    print("Capturando paquetes de red...")
    sniff(prn=packet_callback, filter="ip", store=0)

# Después de la captura, calcula el tiempo de uso
if start_time and end_time:
    usage_time = end_time - start_time
    print(f"Tiempo de uso de Facebook: {usage_time} segundos")
