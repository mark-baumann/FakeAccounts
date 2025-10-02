#!/usr/bin/env python3
"""
Finales Windsurf Registrierungs-Script mit optimierter Cloudflare-Behandlung
"""

import logging
import time
import random
import string
import json
from faker import Faker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from browser.session import BrowserSession

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

fake = Faker()

def generate_password(length=12):
    """Generiert ein sicheres Passwort"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

def detect_cloudflare(driver):
    """Erkennt Cloudflare Challenge"""
    try:
        page_source = driver.page_source.lower()
        title = driver.title.lower()
        url = driver.current_url.lower()
        
        cloudflare_indicators = [
            "cloudflare",
            "checking your browser",
            "ddos protection", 
            "ray id:",
            "cf-ray",
            "please wait",
            "security check",
            "just a moment",
            "browser verification"
        ]
        
        return any(indicator in page_source or indicator in title for indicator in cloudflare_indicators)
    except:
        return False

def wait_for_page_load(driver, timeout=30):
    """Wartet bis die Seite vollständig geladen ist"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except TimeoutException:
        return False

def handle_cloudflare(driver, max_wait=120):
    """Behandelt Cloudflare Challenge automatisch"""
    print("🔍 Prüfe auf Cloudflare Challenge...")
    
    start_time = time.time()
    cloudflare_detected = False
    
    while time.time() - start_time < max_wait:
        if detect_cloudflare(driver):
            if not cloudflare_detected:
                print("🚨 Cloudflare Challenge erkannt!")
                print(f"   URL: {driver.current_url}")
                print(f"   Titel: {driver.title}")
                print("   Warte auf automatische Lösung...")
                cloudflare_detected = True

            # Versuch, die CAPTCHA-Checkbox zu klicken
            try:
                captcha_checkbox = driver.find_element(By.XPATH, '//*[@id="WsTZ8"]/div/label/input')
                if captcha_checkbox.is_displayed():
                    print("   🖱️ Versuche, CAPTCHA-Checkbox zu klicken...")
                    driver.execute_script("arguments[0].click();", captcha_checkbox)
                    print("   ✅ CAPTCHA-Checkbox geklickt. Warte auf Lösung...")
                    time.sleep(5)  # Wartezeit nach dem Klick
            except NoSuchElementException:
                pass # Checkbox nicht gefunden, normaler Wartezyklus
            
            # Warte und prüfe erneut
            time.sleep(3)
            continue
        else:
            if cloudflare_detected:
                print("✅ Cloudflare Challenge erfolgreich bestanden!")
            else:
                print("✅ Keine Cloudflare Challenge erkannt")
            return True
    
    print("⚠️ Cloudflare Challenge Timeout - versuche manuelle Lösung")
    return False

def fill_registration_form(driver):
    """Füllt das Windsurf Registrierungsformular aus"""
    print("📝 Fülle Registrierungsformular aus...")
    
    # Generiere Testdaten
    firstname = fake.first_name()
    lastname = fake.last_name()
    email = "mark.baumann@aman.de"
    password = generate_password()
    
    print(f"   📋 Daten:")
    print(f"      Vorname: {firstname}")
    print(f"      Nachname: {lastname}")
    print(f"      Email: {email}")
    print(f"      Passwort: {password}")

    user_data = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "password": password
    }
    
    try:
        # Warte bis Seite geladen ist
        wait_for_page_load(driver)
        
        # Schritt 1: Grunddaten eingeben
        print("   📝 Schritt 1: Grunddaten...")
        
        # Vorname
        try:
            firstname_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "firstName"))
            )
            firstname_field.clear()
            firstname_field.send_keys(firstname)
            print("      ✅ Vorname eingegeben")
        except TimeoutException:
            print("      ❌ Vorname Feld nicht gefunden")
            return False
        
        # Nachname
        try:
            lastname_field = driver.find_element(By.ID, "lastName")
            lastname_field.clear()
            lastname_field.send_keys(lastname)
            print("      ✅ Nachname eingegeben")
        except NoSuchElementException:
            print("      ❌ Nachname Feld nicht gefunden")
            return False
        
        # Email
        try:
            email_field = driver.find_element(By.ID, "email")
            email_field.clear()
            email_field.send_keys(email)
            print("      ✅ Email eingegeben")
        except NoSuchElementException:
            print("      ❌ Email Feld nicht gefunden")
            return False
        
        # Terms Checkbox
        try:
            terms_checkbox = driver.find_element(By.ID, "terms")
            if not terms_checkbox.is_selected():
                driver.execute_script("arguments[0].click();", terms_checkbox)
                print("      ✅ Terms akzeptiert")
        except NoSuchElementException:
            print("      ⚠️ Terms Checkbox nicht gefunden")
        
        # Continue Button klicken
        print("   🔄 Klicke Continue Button...")
        try:
            continue_btn = driver.find_element(By.XPATH, '/html/body/main/div/div[2]/div/div/div/div[2]/div/div/button[1]')
            driver.execute_script("arguments[0].click();", continue_btn)
            print("      ✅ Continue Button geklickt")
        except NoSuchElementException:
            print("      ❌ Continue Button nicht gefunden")
            return False
        
        # Warte auf nächste Seite
        time.sleep(4)
        wait_for_page_load(driver)
        
        # Schritt 2: Passwort eingeben
        print("   🔐 Schritt 2: Passwort...")
        
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.clear()
            password_field.send_keys(password)
            print("      ✅ Passwort eingegeben")
        except TimeoutException:
            print("      ⚠️ Passwort Feld nicht gefunden - möglicherweise noch auf derselben Seite")
        
        try:
            password_confirm_field = driver.find_element(By.ID, "passwordConfirmation")
            password_confirm_field.clear()
            password_confirm_field.send_keys(password)
            print("      ✅ Passwort Bestätigung eingegeben")
        except NoSuchElementException:
            print("      ⚠️ Passwort Bestätigung Feld nicht gefunden")
        
        print("   ✅ Formular erfolgreich ausgefüllt!")
        return user_data
        
    except Exception as e:
        print(f"   ❌ Fehler beim Ausfüllen: {e}")
        return None

def save_user_data(data, filename="user.json"):
    """Speichert die Benutzerdaten in einer JSON-Datei"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"💾 Benutzerdaten erfolgreich in '{filename}' gespeichert.")
    except IOError as e:
        print(f"❌ Fehler beim Speichern der Datei: {e}")

def main():
    """Hauptfunktion"""
    url = "https://windsurf.com/account/register"
    
    print("🚀 Starte Windsurf Registrierung...")
    print(f"🎯 Ziel-URL: {url}")
    
    # Browser starten (ohne Tor für bessere Cloudflare-Kompatibilität)
    print("🌐 Starte Browser...")
    browser = BrowserSession(tor_proxy=None)
    if not browser.start():
        print("❌ Browser konnte nicht gestartet werden")
        return
    
    driver = browser.driver
    
    try:
        print(f"📡 Lade Seite: {url}")
        driver.get(url)
        
        # Cloudflare Challenge behandeln
        if not handle_cloudflare(driver):
            print("❌ Manuelle Cloudflare-Lösung erforderlich. Breche ab.")
            return # Exit main function if manual intervention is needed
        
        print(f"📍 Aktuelle URL: {driver.current_url}")
        print(f"📄 Seitentitel: {driver.title}")
        
        # Prüfe nochmal auf Cloudflare nach manueller Eingabe
        if detect_cloudflare(driver):
            print("⚠️ Cloudflare immer noch aktiv - warte weitere 10 Sekunden...")
            time.sleep(10)
        
        # Registrierungsformular ausfüllen
        user_data = fill_registration_form(driver)
        
        if user_data:
            print("\n🎉 Registrierung erfolgreich ausgefüllt!")
            save_user_data(user_data)
        else:
            print("\n❌ Fehler bei der Registrierung")
        
        # Warte kurz, um sicherzustellen, dass alle Aktionen abgeschlossen sind
        print("\n✅ Registrierungsprozess abgeschlossen. Warte 5 Sekunden vor dem Schließen.")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n🛑 Script durch Benutzer abgebrochen")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
        print(f"❌ Unerwarteter Fehler: {e}")
    finally:
        print("🧹 Browser wird geschlossen...")
        browser.close()
        print("✅ Fertig!")

if __name__ == "__main__":
    main()
