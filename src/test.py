from scapy.all import sniff, TCP, IP
import socket

def packet_callback(packet):
    # Verifica si el paquete es TCP y si el puerto de destino es 443 (HTTPS)

    if TCP in packet and packet[TCP].dport == 443:
        # Intenta extraer el host del paquete IP
        try:
            ip_address = packet[IP].dst
            # Traduce la dirección IP a un nombre de dominio
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            print("\nhostname: " + hostname)
            # Busca si el nombre de dominio contiene "facebook.com"
            if "facebook.com" in hostname:
                print("Se ha detectado una conexión a Facebook:", packet.summary())
        except socket.herror:
            # Maneja el caso en que la dirección IP no tenga un nombre de dominio asociado
            pass

if __name__ == "__main__":
    print("Capturando paquetes de red...")
    sniff(prn=packet_callback, filter="ip")
