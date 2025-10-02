#!/usr/bin/env python3
"""
Tor Installer für Windows - Lädt Tor Browser herunter und extrahiert tor.exe
"""

import os
import sys
import requests
import zipfile
import tempfile
from pathlib import Path

class TorInstaller:
    def __init__(self):
        self.tor_dir = Path(__file__).parent / "tor_files"
        self.tor_exe = self.tor_dir / "tor.exe"
        
    def is_tor_installed(self):
        """Prüft ob tor.exe bereits vorhanden ist"""
        return self.tor_exe.exists()
    
    def download_tor_expert_bundle(self):
        """Lädt Tor Expert Bundle für Windows herunter"""
        print("Lade Tor Expert Bundle herunter...")
        
        # Tor Expert Bundle URL (Windows 64-bit)
        url = "https://archive.torproject.org/tor-package-archive/torbrowser/12.5.6/tor-expert-bundle-12.5.6-windows-x86_64.tar.gz"
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Temporäre Datei erstellen
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            print(f"Download abgeschlossen: {tmp_path}")
            return tmp_path
            
        except Exception as e:
            print(f"Fehler beim Download: {e}")
            return None
    
    def extract_tor(self, archive_path):
        """Extrahiert tor.exe aus dem Archiv"""
        print("Extrahiere Tor...")
        
        try:
            import tarfile
            
            # Zielverzeichnis erstellen
            self.tor_dir.mkdir(exist_ok=True)
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                # Suche nach tor.exe in dem Archiv
                for member in tar.getmembers():
                    if member.name.endswith('tor.exe'):
                        print(f"Gefunden: {member.name}")
                        # Extrahiere tor.exe
                        member.name = "tor.exe"  # Umbenenne zu einfachem Namen
                        tar.extract(member, self.tor_dir)
                        break
                else:
                    print("tor.exe nicht im Archiv gefunden")
                    return False
            
            # Aufräumen
            os.unlink(archive_path)
            print(f"Tor installiert in: {self.tor_exe}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Extrahieren: {e}")
            return False
    
    def install_tor(self):
        """Installiert Tor falls nicht vorhanden"""
        if self.is_tor_installed():
            print(f"Tor bereits installiert: {self.tor_exe}")
            return str(self.tor_exe)
        
        print("Tor nicht gefunden. Installiere Tor...")
        
        archive_path = self.download_tor_expert_bundle()
        if not archive_path:
            return None
        
        if self.extract_tor(archive_path):
            return str(self.tor_exe)
        
        return None
    
    def get_tor_path(self):
        """Gibt den Pfad zu tor.exe zurück"""
        return str(self.tor_exe) if self.is_tor_installed() else None

def main():
    installer = TorInstaller()
    tor_path = installer.install_tor()
    
    if tor_path:
        print(f"✓ Tor verfügbar: {tor_path}")
    else:
        print("✗ Tor Installation fehlgeschlagen")

if __name__ == "__main__":
    main()
