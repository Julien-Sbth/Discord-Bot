import sqlite3
import logging
from datetime import datetime

def init_db():
    conn = sqlite3.connect("bot_offres.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        titre TEXT,
        entreprise TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidatures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        offre_url TEXT UNIQUE,
        entreprise TEXT,
        statut TEXT DEFAULT "en attente",
        commentaires TEXT,
        date_postulation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def enregistrer_candidature(url, entreprise, statut="en attente", commentaires=None):
    try:
        with sqlite3.connect("bot_offres.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO candidatures 
                (offre_url, entreprise, statut, commentaires, date_postulation)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(offre_url) DO UPDATE SET
                    statut = excluded.statut,
                    commentaires = excluded.commentaires
            """, (url, entreprise, statut, commentaires or "", datetime.now()))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erreur DB: {str(e)}")
        raise

def recuperer_offres_disponibles():
    conn = sqlite3.connect("bot_offres.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT url, titre, entreprise FROM offres
        WHERE url NOT IN (SELECT offre_url FROM candidatures)
    """)

    offres = cursor.fetchall()
    conn.close()

    return offres
