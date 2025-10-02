#!/usr/bin/env python3
"""
Verbesserte Tor Proxy Klasse mit automatischer Installation
"""

import platform
import subprocess
import time
import requests
import tempfile
import os
from pathlib import Path
from .tor_installer import TorInstaller

class TorProxyImproved:
    """
    Verbesserte Tor-Proxy Klasse mit automatischer Installation
    """
    
    def __init__(self, socks_port=9050, control_port=9051):
        self.socks_port = socks_port
        self.control_port = control_port
        self.tor_process = None
        self.tor_exe = None
        self.data_dir = None
        
        # Tor-Installation prüfen/installieren
        installer = TorInstaller()
        self.tor_exe = installer.install_tor()
        
        if not self.tor_exe:
            print("⚠ Tor konnte nicht installiert werden")
            # Fallback: Versuche Tor im System zu finden
            self.tor_exe = self._find_system_tor()
    
    def _find_system_tor(self):
        """Versucht Tor im System zu finden"""
        possible_paths = [
            "tor",
            "tor.exe", 
            r"C:\Program Files\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
            r"C:\Users\{}\AppData\Local\Tor Browser\Browser\TorBrowser\Tor\tor.exe".format(os.getenv('USERNAME', '')),
            "/usr/bin/tor",
            "/usr/local/bin/tor"
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    print(f"✓ Tor gefunden: {path}")
                    return path
            except:
                continue
        
        return None
    
    def _create_tor_config(self):
        """Erstellt eine temporäre Tor-Konfiguration"""
        self.data_dir = tempfile.mkdtemp(prefix="tor_data_")
        
        config_content = f"""
SocksPort {self.socks_port}
ControlPort {self.control_port}
DataDirectory {self.data_dir}
ExitPolicy reject *:*
Log notice stdout
"""
        
        config_path = os.path.join(self.data_dir, "torrc")
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        return config_path
    
    def start(self):
        """Startet Tor mit temporärer Konfiguration"""
        if not self.tor_exe:
            print("✗ Tor executable nicht gefunden")
            return False
        
        print(f"[TorProxy] Starte Tor mit {self.tor_exe}...")
        
        try:
            config_path = self._create_tor_config()
            
            # Tor mit Konfigurationsdatei starten
            self.tor_process = subprocess.Popen([
                self.tor_exe,
                "-f", config_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Warte auf Tor-Startup (prüfe SOCKS Port)
            print("Warte auf Tor-Startup...")
            for i in range(30):  # 30 Sekunden Timeout
                if self._test_socks_connection():
                    print(f"✓ Tor läuft auf Port {self.socks_port}")
                    return True
                time.sleep(1)
                
                # Prüfe ob Prozess noch läuft
                if self.tor_process.poll() is not None:
                    stdout, stderr = self.tor_process.communicate()
                    print(f"✗ Tor Prozess beendet. Stderr: {stderr.decode()}")
                    return False
            
            print("✗ Tor-Start Timeout")
            return False
            
        except Exception as e:
            print(f"✗ Fehler beim Starten: {e}")
            return False
    
    def _test_socks_connection(self):
        """Testet ob SOCKS Proxy verfügbar ist"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', self.socks_port))
            sock.close()
            return result == 0
        except:
            return False
    
    def stop(self):
        """Stoppt Tor und räumt auf"""
        if self.tor_process:
            print("[TorProxy] Stoppe Tor...")
            self.tor_process.terminate()
            
            # Warte auf sauberes Beenden
            try:
                self.tor_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.tor_process.kill()
        
        # Temporäre Dateien aufräumen
        if self.data_dir and os.path.exists(self.data_dir):
            import shutil
            try:
                shutil.rmtree(self.data_dir)
            except:
                pass
    
    def get_proxy_url(self):
        """Gibt SOCKS Proxy URL zurück"""
        return f"socks5://127.0.0.1:{self.socks_port}"
    
    def get_exit_ip(self):
        """Ermittelt die Exit-IP über Tor"""
        try:
            proxies = {
                "http": self.get_proxy_url(),
                "https": self.get_proxy_url()
            }
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
            data = response.json()
            return data.get("origin", "Unknown")
        except Exception as e:
            print(f"Fehler bei get_exit_ip: {e}")
            return "Unknown"
    
    def test_connection(self):
        """Testet die Tor-Verbindung"""
        print("Teste Tor-Verbindung...")
        
        # Test 1: SOCKS Port
        if not self._test_socks_connection():
            print("✗ SOCKS Port nicht erreichbar")
            return False
        
        print("✓ SOCKS Port erreichbar")
        
        # Test 2: Exit IP
        exit_ip = self.get_exit_ip()
        if exit_ip != "Unknown":
            print(f"✓ Exit IP: {exit_ip}")
            return True
        else:
            print("✗ Exit IP nicht ermittelbar")
            return False

# Test-Funktion
def main():
    tor = TorProxyImproved()
    
    if tor.start():
        print("✓ Tor erfolgreich gestartet")
        tor.test_connection()
        
        input("Drücke Enter zum Beenden...")
        tor.stop()
    else:
        print("✗ Tor konnte nicht gestartet werden")

if __name__ == "__main__":
    main()
