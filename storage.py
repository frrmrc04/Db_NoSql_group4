# storage.py

import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, RECENT_LIMIT

# Connessione Redis
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True  # Per ottenere stringhe direttamente
)

def save_notification(channel: str, message_json: str):
    """
    Salva la notifica nella lista delle notifiche recenti del canale.
    Mantiene solo le ultime RECENT_LIMIT notifiche.
    """
    pipe = r.pipeline()
    pipe.lpush(f"recent:{channel}", message_json)
    pipe.ltrim(f"recent:{channel}", 0, RECENT_LIMIT - 1)
    pipe.execute()

def get_recent_notifications(channel: str):
    """
    Recupera le ultime notifiche del canale come lista di stringhe JSON.
    """
    return r.lrange(f"recent:{channel}", 0, RECENT_LIMIT - 1)
