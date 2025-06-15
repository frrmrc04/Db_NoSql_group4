# auth.py

import redis

# Connessione Redis
r = redis.Redis(decode_responses=True)

def accesso():
    """
    Effettua il login di un utente registrato.
    Restituisce l'username se il login ha successo, altrimenti None.
    """
    username = input("Username: ").strip()
    if not username:
        print("⚠️ Devi inserire un username.")
        return None

    if not r.sismember("utenti_reg", username):
        print("❌ Utente non trovato.")
        return None

    password = input("Password: ").strip()
    user_dict = r.hgetall(f'utenti:{username}')
    
    if password != user_dict.get('pass'):
        print("❌ Password errata.")
        return None

    print(f"✅ Login riuscito. Benvenuto {username}!")
    return username


def registrazione():
    """
    Registra un nuovo utente. Ritorna l'username appena registrato.
    """
    while True:
        username = input("Scegli un username: ").strip()
        if not username:
            print("⚠️ Inserire un nome utente valido.")
        elif r.sismember("utenti_reg", username):
            print("⚠️ Nome utente già esistente. Scegline un altro.")
        else:
            break

    while True:
        password = input("Scegli una password: ").strip()
        if password:
            break
        print("⚠️ Inserisci una password valida.")

    r.sadd("utenti_reg", username)
    r.hset(f"utenti:{username}", mapping={'pass': password})
    print(f"✅ Registrazione completata. Benvenuto {username}!")
    return username


def get_user_channels(username):
    """
    Restituisce la lista dei canali a cui l'utente è sottoscritto.
    """
    return list(r.smembers(f"user:{username}:channels"))


def subscribe_channel(username, channel):
    """
    Aggiunge un canale alle sottoscrizioni dell'utente.
    """
    r.sadd(f"user:{username}:channels", channel)


def unsubscribe_channel(username, channel):
    """
    Rimuove un canale dalle sottoscrizioni dell'utente.
    """
    r.srem(f"user:{username}:channels", channel)
