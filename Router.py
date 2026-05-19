import requests
import time
from ncclient import manager
from ncclient.operations import RPCError

# --- Verbindingsinstellingen ---
HOST     = "10.10.10.1"
PORT     = 830
USERNAME = "student"
PASSWORD = "pxl"

# --- GitHub URL (Single Source of Truth) ---
GITHUB_RAW_URL = "https://raw.githubusercontent.com/JoachimMorisPXL/Code-Router/refs/heads/main/taak-36.xml"
CHECK_INTERVAL = 300  # 5 minuten (in seconden)

def haal_config_op_van_github(url):
    """Haal XML configuratie op uit GitHub."""
    print(f"[*] Config ophalen van: {url}")
    try:
        # Cache uitschakelen met headers om zeker te zijn van de nieuwste versie
        headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[-] Fout bij ophalen GitHub configuratie: {e}")
        raise

def deploy_via_netconf(config_xml):
    """Deploy de configuratie via NETCONF (Direct naar running)."""
    print(f"[*] Verbinden met router {HOST} via NETCONF...")
    
    with manager.connect(
        host=HOST, port=PORT,
        username=USERNAME, password=PASSWORD,
        hostkey_verify=False
    ) as m:
        print("[+] Verbonden met de router.")
        
        try:
            # We schrijven direct naar de 'running' datastore omdat
            # de lab-router de 'candidate' functionaliteit niet ondersteunt.
            print("[*] Configuratie direct wegschrijven naar 'running' datastore...")
            m.edit_config(target="running", config=config_xml)
            
            print("[+] SUCCES: Deployment is geslaagd! Configuratie is actief.")
            
        except RPCError as e:
            print(f"[-] Fout in XML configuratie of router weigert: {e.message}")
        except Exception as e:
            print(f"[-] Onverwachte fout tijdens deployment: {e}")

# --- Hoofdprogramma ---
if __name__ == "__main__":
    laatste_config = None  # Variabele om de vorige status bij te houden
    
    print("[*] Script gestart. Polling elke 5 minuten...")
    
    while True:
        huidige_tijd = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{huidige_tijd}] Controle op nieuwe configuratie...")
        
        try:
            # 1. Haal de (mogelijk nieuwe) configuratie op
            huidige_config = haal_config_op_van_github(GITHUB_RAW_URL)
            
            # 2. Vergelijk met de laatst bekende configuratie
            if huidige_config != laatste_config:
                if laatste_config is None:
                    print("[+] Eerste run: initiÃ«le configuratie pushen...")
                else:
                    print("[+] Wijziging gedetecteerd op GitHub! Nieuwe configuratie pushen...")
                
                # 3. Deploy naar de router
                deploy_via_netconf(huidige_config)
                
                # 4. Update de laatst bekende configuratie
                laatste_config = huidige_config
            else:
                print("[*] Geen wijzigingen op GitHub. Er wordt niets gepusht.")
                
        except Exception as e:
            print(f"[-] Loop afgebroken door fout: {e}. Volgende poging in 5 minuten.")
            
        # 5. Wacht 5 minuten (300 seconden)
        time.sleep(CHECK_INTERVAL)
