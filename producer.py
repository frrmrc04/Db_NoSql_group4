from datetime import datetime
import redis
import json
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, RECENT_LIMIT

# Connessione Redis
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

# ------------------ INVIO NOTIFICHE ------------------ #
def crea_notifica():
    mostra_canali()
    canale = input("Canale di destinazione: ").strip()

    if not r.sismember("canali_disponibili", canale):
        print(f"❌ Il canale '{canale}' non esiste. Usa la gestione canali per crearlo.")
        return None, None

    titolo = input("Titolo: ").strip()
    messaggio = input("Messaggio: ").strip()
    timestamp = datetime.now().isoformat(timespec='seconds')

    notifica = {
        "timestamp": timestamp,
        "titolo": titolo,
        "messaggio": messaggio,
        "canale": canale
    }

    return canale, json.dumps(notifica)

def invia_notifica(canale, notifica_json):
    pipe = r.pipeline()
    pipe.publish(canale, notifica_json)
    pipe.lpush(f"recent:{canale}", notifica_json)
    pipe.ltrim(f"recent:{canale}", 0, RECENT_LIMIT - 1)
    pipe.execute()
    print("✅ Notifica inviata con successo.")

def menu_notifiche():
    while True:
        canale, notifica = crea_notifica()
        if canale and notifica:
            invia_notifica(canale, notifica)

        again = input("Inviare un'altra notifica? (s/n): ").strip().lower()
        if again != 's':
            break

# ------------------ GESTIONE CANALI ------------------ #
def aggiungi_canale():
    canale = input("Nome nuovo canale: ").strip()
    if r.sismember("canali_disponibili", canale):
        print("⚠️ Canale già esistente.")
    else:
        r.sadd("canali_disponibili", canale)
        print(f"✅ Canale '{canale}' aggiunto.")

def rimuovi_canale():
    canale = input("Nome canale da rimuovere: ").strip()
    if r.sismember("canali_disponibili", canale):
        r.srem("canali_disponibili", canale)
        print(f"🗑️ Canale '{canale}' rimosso.")
    else:
        print("❌ Canale non trovato.")

def mostra_canali():
    canali = sorted(r.smembers("canali_disponibili"))
    if not canali:
        print("ℹ️ Nessun canale disponibile.")
        return
    print("\n📡 Canali disponibili:")
    for c in canali:
        print("-", c)

def menu_canali():
    while True:
        print("\n--- Gestione Canali ---")
        print("1. Aggiungi canale")
        print("2. Rimuovi canale")
        print("3. Mostra canali")
        print("4. Torna al menu principale")
        scelta = input("> ").strip()

        if scelta == "1":
            aggiungi_canale()
        elif scelta == "2":
            rimuovi_canale()
        elif scelta == "3":
            mostra_canali()
        elif scelta == "4":
            break
        else:
            print("❌ Scelta non valida.")

# ------------------ MENU PRINCIPALE ------------------ #
def main():
    print("🟢 PRODUTTORE DI NOTIFICHE")
    while True:
        print("\n--- Menu Principale ---")
        print("1. Invia notifiche")
        print("2. Gestione canali")
        print("3. Esci")
        scelta = input("> ").strip()

        if scelta == "1":
            menu_notifiche()
        elif scelta == "2":
            menu_canali()
        elif scelta == "3":
            print("👋 Uscita dal produttore.")
            break
        else:
            print("❌ Scelta non valida.")

if __name__ == "__main__":
    main()
