import sqlite3
import logging
from datetime import datetime


def init_db():
    try:
        conn = sqlite3.connect("Database/bot_offres.db")
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
            offre_url TEXT,
            entreprise TEXT,
            statut TEXT,
            commentaires TEXT,
            date_postulation NUM,
            nom_poste TEXT
        )
        """)

        conn.commit()
        logging.info("Base de données et tables créées avec succès (si elles n'existaient pas).")

    except sqlite3.Error as e:
        logging.error(f"Erreur lors de la création des tables ou de la connexion à la base de données : {e}")

    finally:
        conn.close()


def enregistrer_candidature(url, entreprise, statut="en attente", commentaires=None):
    try:
        with sqlite3.connect("Database/bot_offres.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO candidatures 
                (offre_url, entreprise, statut, commentaires, date_postulation)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(offre_url) DO UPDATE SET
                    statut = excluded.statut,
                    commentaires = excluded.commentaires,
                    date_postulation = excluded.date_postulation
            """, (url, entreprise, statut, commentaires or "", datetime.now()))
            conn.commit()
            logging.info(f"Candidature pour {entreprise} enregistrée avec le statut {statut}.")
    except sqlite3.Error as e:
        logging.error(f"Erreur DB lors de l'enregistrement de la candidature : {str(e)}")
        raise


def recuperer_offres_disponibles():
    try:
        conn = sqlite3.connect("Database/bot_offres.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT url, titre, entreprise FROM offres
            WHERE url NOT IN (SELECT offre_url FROM candidatures)
        """)

        offres = cursor.fetchall()
        logging.info(f"{len(offres)} offres disponibles récupérées.")
        return offres
    except sqlite3.Error as e:
        logging.error(f"Erreur DB lors de la récupération des offres : {str(e)}")
        return []
    finally:
        conn.close()