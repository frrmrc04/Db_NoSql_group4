import redis
import json
from time import sleep
import threading
import datetime
from datetime import datetime, timedelta

import autentication as aut  # assicurati che il file si chiami autentication.py
from storage import get_recent_notifications
from config import REDIS_HOST, REDIS_PORT, REDIS_DB


def ascolta_in_thread(canali):
    t = threading.Thread(target=ascolta_in_tempo_reale, args=(canali,), daemon=True)
    t.start()
    return t

# Connessione Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def mostra_notifiche_recenti(canali):
    print("\n🕓 Ultime notifiche recenti:")
    limite_orario = datetime.now() - timedelta(hours=10)

    for canale in canali:
        print(f"\n📣 Canale: {canale}")
        notifiche = get_recent_notifications(canale)
        notifiche_filtrate = []

        for n in reversed(notifiche):
            dati = json.loads(n)
            try:
                ts = datetime.fromisoformat(dati['timestamp'])
                if ts >= limite_orario:
                    notifiche_filtrate.append(dati)
            except ValueError:
                continue  # Salta se il timestamp è malformato

        if notifiche_filtrate:
            for dati in notifiche_filtrate:
                print(f"[{dati['timestamp']}] {dati['titolo']}: {dati['messaggio']}")
        else:
            print("🕓 Nessuna notifica recente (entro 10 ore).")



def ascolta_in_tempo_reale(canali):
    print("\n🔴 Ascolto attivo. In attesa di nuove notifiche...\n(CTRL+C per uscire)\n")
    pubsub = r.pubsub()
    pubsub.subscribe(*canali)

    try:
        for msg in pubsub.listen():
            if msg["type"] == "message":
                dati = json.loads(msg["data"])
                print(f"\n🆕 [{dati['timestamp']}] 📢 {dati['canale']}: {dati['titolo']} → {dati['messaggio']}")
    except KeyboardInterrupt:
        print("\n👋 Uscita dal consumer.")

def iscriviti_a_un_canale(username):
    canali_disponibili = sorted(r.smembers("canali_disponibili"))
    
    if not canali_disponibili:
        print("⚠️ Nessun canale disponibile. Chiedi a un producer di crearne uno.")
        return

    print("\n📡 Canali disponibili:")
    for i, c in enumerate(canali_disponibili, 1):
        print(f"{i}. {c}")

    scelta = input("Scegli un numero di canale da sottoscrivere: ").strip()

    if not scelta.isdigit() or not (1 <= int(scelta) <= len(canali_disponibili)):
        print("❌ Scelta non valida.")
        return

    canale_scelto = canali_disponibili[int(scelta) - 1]
    r.sadd(f"user:{username}:channels", canale_scelto)
    print(f"✅ Ti sei iscritto al canale: '{canale_scelto}'")

def main():
    print("🔵 CONSUMATORE DI NOTIFICHE")
    username = aut.accesso()
    if not username:
        print("❌ Accesso fallito.")
        aut.registrazione()
    

    canali = aut.get_user_channels(username)
    if not canali:
        print("⚠️ Non sei iscritto a nessun canale.")
        iscriviti_a_un_canale(username)
        canali = aut.get_user_channels(username)
        if not canali:
            print("❌ Nessun canale selezionato. Uscita.")
            return

    mostra_notifiche_recenti(canali)
    ascolta_in_tempo_reale(canali)

    # Il thread principale resta interattivo
    try:
        while True:
            comando = input("\nScrivi 'canali' per gestire iscrizioni o 'esci' per uscire: ").strip().lower()
            if comando == "esci":
                print("👋 Uscita dal consumer.")
                break
            elif comando == "canali":
                iscriviti_a_un_canale(username)
                canali = aut.get_user_channels(username)
            else:
                print("❓ Comando non riconosciuto.")
    except KeyboardInterrupt:
        print("\n👋 Interrotto manualmente.")


if __name__ == "__main__":
    main()



