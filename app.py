import streamlit as st
import redis
import json
from datetime import datetime, timedelta

from config import REDIS_HOST, REDIS_PORT, REDIS_DB
from storage import get_recent_notifications
#from autentication import registrazione
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

# ----------------------- AUTENTICAZIONE -----------------------
def login(username, password):
    if not r.sismember("utenti_reg", username):
        return False
    user_data = r.hgetall(f"utenti:{username}")
    return user_data.get("pass") == password

def get_user_channels(username):
    return list(r.smembers(f"user:{username}:channels"))

def get_all_channels():
    return sorted(r.smembers("canali_disponibili"))

def subscribe_channel(username, channel):
    r.sadd(f"user:{username}:channels", channel)

# ----------------------- STREAMLIT UI -----------------------
st.set_page_config(page_title="Notifiche Redis", layout="centered")

st.title("📢 Sistema di Notifiche Redis")
st.caption("Visualizza solo le notifiche inviate nelle ultime 10 ore.")

# ----------------------- LOGIN -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    login_tab, register_tab = st.tabs(["Accedi", "Registrati"])

    with login_tab:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Accedi"):
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Benvenuto, {username}!")
                st.rerun()
            else:
                st.error("❌ Username o password errati.")

    with register_tab:
        new_user = st.text_input("Nuovo username", key="reg_user")
        new_pass = st.text_input("Nuova password", type="password", key="reg_pass")
        if st.button("Registrati"):
            if not new_user or not new_pass:
                st.warning("⚠️ Compila tutti i campi.")
            elif r.sismember("utenti_reg", new_user):
                st.error("⚠️ Nome utente già esistente.")
            else:
                r.sadd("utenti_reg", new_user)
                r.hset(f"utenti:{new_user}", mapping={"pass": new_pass})
                st.success(f"✅ Registrazione completata per {new_user}! Ora puoi accedere.")

# ----------------------- HOME -----------------------

username = st.session_state.get("username")
if username:
    st.success(f"✅ Accesso come **{username}**")
    user_channels = get_user_channels(st.session_state.username)

    # Iscrizione a nuovi canali
    with st.expander("➕ Iscriviti a nuovi canali"):
        all_channels = get_all_channels()
        canali_non_sottoscritti = [c for c in all_channels if c not in user_channels]

        if canali_non_sottoscritti:
            nuovo_canale = st.selectbox("Scegli un canale disponibile:", canali_non_sottoscritti)
            if st.button("Iscriviti"):
                subscribe_channel(st.session_state.username, nuovo_canale)
                st.success(f"✅ Iscritto al canale: {nuovo_canale}")
                st.rerun()
        else:
            st.info("✔️ Sei già iscritto a tutti i canali disponibili.")

    # Visualizza notifiche recenti
    st.subheader("🕓 Notifiche recenti (ultime 10 ore)")
    limite = datetime.now() - timedelta(hours=10)

    if not user_channels:
        st.warning("⚠️ Non sei iscritto a nessun canale.")
    else:
        for canale in user_channels:
            with st.expander(f"📡 {canale}"):
                raw = get_recent_notifications(canale)
                count = 0
                for item in reversed(raw):
                    try:
                        dati = json.loads(item)
                        ts = datetime.fromisoformat(dati["timestamp"])
                        if ts >= limite:
                            with st.container():
                                st.markdown(f"**🕘 {dati['timestamp']}** — **{dati['titolo']}**")
                                st.write(dati["messaggio"])
                                st.divider()
                            count += 1
                    except Exception:
                        continue
                if count == 0:
                    st.info("🕓 Nessuna notifica negli ultimi 10 ore.")