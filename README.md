# Db_NoSql_group4

**Documentazione Tecnica - Sistema di Notifiche Redis**

**Panoramica del Sistema**

Il sistema implementa un'architettura di notifiche distribuita basata su Redis, seguendo il pattern **Publisher-Subscriber** con persistenza delle notifiche recenti. Il sistema supporta due modalità di utilizzo: interfaccia a riga di comando (CLI) e interfaccia web tramite Streamlit.

**Pattern Architetturali**

- **Publisher-Subscriber**: Per la distribuzione in tempo reale delle notifiche
- **Repository Pattern**: Attraverso il modulo storage.py per l'astrazione dei dati
- **Separation of Concerns**: Ogni modulo ha responsabilità specifiche
- **Configuration Pattern**: Centralizzazione delle configurazioni in config.py

**Organizzazione delle Chiavi**

\# Gestione utenti

utenti\_reg                      # SET: lista degli username registrati

utenti:{username}               # HASH: dati utente (password, etc.)

user:{username}:channels        # SET: canali sottoscritti dall'utente

\# Gestione canali

canali\_disponibili              # SET: tutti i canali esistenti nel sistema

recent:{channel}                # LIST: ultime 10 notifiche del canale

\# Pub/Sub

{channel}                       # CHANNEL: canale di pubblicazione Redis

**Formato delle Notifiche**

Le notifiche sono serializzate in formato JSON:

{

`    `"timestamp": "2025-06-15T14:30:25",

`    `"titolo": "Titolo della notifica",

`    `"messaggio": "Contenuto del messaggio",

`    `"canale": "nome\_canale"

}

**Implementazione dei Moduli**

**1. config.py**

**Responsabilità**: Centralizzazione delle configurazioni di sistema

REDIS\_HOST = 'localhost'    # Host del server Redis

REDIS\_PORT = 6379          # Porta di connessione

REDIS\_DB = 0               # Database Redis (0-15)

RECENT\_LIMIT = 10          # Numero massimo di notifiche recenti per canale

**Scelte tecniche**:

- Configurazioni hardcoded per semplicità
- Possibilità di estensione con variabili d'ambiente

**2. storage.py**

**Responsabilità**: Astrazione dell'accesso ai dati Redis

**Funzioni principali**:

- save\_notification(): Salva notifiche con rotazione automatica
- get\_recent\_notifications(): Recupera cronologia notifiche

**Implementazione chiave**:

def save\_notification(channel: str, message\_json: str):

`    `pipe = r.pipeline()

`    `pipe.lpush(f"recent:{channel}", message\_json)

`    `pipe.ltrim(f"recent:{channel}", 0, RECENT\_LIMIT - 1)

`    `pipe.execute()

**Scelte tecniche**:

- Uso di **Redis Pipeline** per operazioni atomiche
- **LPUSH + LTRIM** per mantenere solo le notifiche recenti
- **decode\_responses=True** per semplificare la gestione delle stringhe

**3. autentication.py**

**Responsabilità**: Gestione dell'autenticazione e sottoscrizioni utenti

**Funzioni principali**:

- accesso(): Login interattivo
- registrazione(): Registrazione nuovo utente
- get\_user\_channels(): Recupera sottoscrizioni utente
- subscribe\_channel() / unsubscribe\_channel(): Gestione sottoscrizioni

**Scelte tecniche**:

- Password in chiaro (da migliorare in produzione)
- Uso di Redis SET per gestire sottoscrizioni utente
- Validazione input basilare

**4. producer.py**

**Responsabilità**: Interfaccia per la creazione e invio di notifiche

**Funzionalità**:

- Gestione canali (creazione, rimozione, visualizzazione)
- Creazione e invio notifiche
- Menu interattivo CLI

**Implementazione invio**:

def invia\_notifica(canale, notifica\_json):

`    `pipe = r.pipeline()

`    `pipe.publish(canale, notifica\_json)           # Pub/Sub immediato

`    `pipe.lpush(f"recent:{canale}", notifica\_json) # Persistenza

`    `pipe.ltrim(f"recent:{canale}", 0, RECENT\_LIMIT - 1)

`    `pipe.execute()

**Scelte tecniche**:

- **Doppia scrittura**: Pub/Sub + persistenza atomica
- Validazione esistenza canale prima dell'invio
- Timestamp ISO 8601 per compatibilità

**5. consumer.py**

**Responsabilità**: Interfaccia per la ricezione di notifiche

**Funzionalità**:

- Visualizzazione notifiche recenti (ultime 10 ore)
- Ascolto in tempo reale tramite Redis Pub/Sub
- Gestione sottoscrizioni interattiva

**Implementazione ascolto**:

def ascolta\_in\_tempo\_reale(canali):

`    `pubsub = r.pubsub()

`    `pubsub.subscribe(\*canali)



`    `for msg in pubsub.listen():

`        `if msg["type"] == "message":

`            `dati = json.loads(msg["data"])

`            `print(f"🆕 [{dati['timestamp']}] 📢 {dati['canale']}: {dati['titolo']}")

**Scelte tecniche**:

- **Threading** per ascolto non-bloccante
- Filtro temporale per notifiche recenti (10 ore)
- Gestione graceful di KeyboardInterrupt

**6. app.py (Streamlit)**

**Responsabilità**: Interfaccia web per utenti finali

**Funzionalità**:

- Sistema di login/registrazione web
- Gestione sottoscrizioni tramite UI
- Visualizzazione notifiche con filtro temporale
- Interfaccia responsive

**Scelte tecniche**:

- **Streamlit session state** per gestione sessioni
- **st.rerun()** per aggiornamenti interfaccia
- **Expander** per organizzazione contenuti
- Filtro temporale client-side per performance

**7. init.py**

**Responsabilità**: Entry point per modalità CLI

Semplice dispatcher che indirizza verso producer o consumer basato sull'input utente.

**Scelte Tecniche Significative**

**1. Redis come Message Broker**

**Vantaggi**:

- Pub/Sub nativo ad alte performance
- Persistenza dati integrata
- Strutture dati ricche (SET, LIST, HASH)
- Operazioni atomiche tramite pipeline

**Limitazioni**:

- Single point of failure
- Persistenza limitata (non durabile come database relazionali)

**2. Doppia Scrittura (Pub/Sub + Persistenza)**

pipe.publish(canale, notifica\_json)           # Tempo reale

pipe.lpush(f"recent:{canale}", notifica\_json) # Persistenza

**Motivazione**: Garantire sia la consegna immediata che la possibilità di recuperare notifiche perse.

**3. Filtro Temporale (10 ore)**

**Implementazione**: Filtro applicato sia lato server che client **Motivazione**: Bilanciare performance e utilità per l'utente

**4. Gestione Errori Minimalista**

**Scelta**: Gestione di base con try/catch **Motivazione**: Semplicità per prototipo, da migliorare in produzione

**Modalità di Utilizzo**

**Modalità CLI**

**Avvio del Sistema**

python init.py

**Come Producer**

1. Selezionare "producer"
1. Gestire canali (Menu 2)
1. Creare notifiche (Menu 1)

**Come Consumer**

1. Selezionare "user"
1. Effettuare login/registrazione
1. Sottoscriversi ai canali
1. Visualizzare notifiche recenti e in tempo reale

**Modalità Web (Streamlit)**

**Avvio**

streamlit run app.py

**Utilizzo**

1. Accedere via browser
1. Login/registrazione tramite interfaccia web
1. Gestire sottoscrizioni nella sezione dedicata
1. Visualizzare notifiche recenti automaticamente

**Requisiti del Sistema**

**Dipendenze Python**

streamlit>=1.28.0

redis>=4.5.0

**Infrastruttura**

- Redis Server (versione 6.0+)
- Python 3.8+
- Connessione di rete per modalità distribuita

**Configurazione Redis**

\# Configurazione minima redis.conf

maxmemory-policy allkeys-lru

save 900 1

save 300 10

save 60 10000

**Limitazioni e Miglioramenti Futuri**

**Limitazioni Attuali**

1. **Sicurezza**: Password in chiaro, nessuna validazione robusta
1. **Scalabilità**: Single Redis instance
1. **Monitoring**: Nessun logging strutturato
1. **Error Handling**: Gestione errori basilare

