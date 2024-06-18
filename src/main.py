import requests

def check_facebook_connection():
    url = 'https://www.facebook.com'
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("Conexión a Facebook detectada.")
            return True
        else:
            print("Error al conectar con Facebook. Código de estado:", response.status_code)
            return False
    except requests.ConnectionError:
        print("No se pudo conectar con Facebook.")
        return False

# Prueba la función
if check_facebook_connection():
    print("Puedes acceder a Facebook.")
else:
    print("No puedes acceder a Facebook.")
