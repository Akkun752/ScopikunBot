import pymysql
import os
import re
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_IP"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWD"),
        database=os.getenv("DB_DB"),
        cursorclass=pymysql.cursors.DictCursor # Utilisation de DictCursor pour lire par nom de colonne
    )

def get_pokemon_data(query_text, forme_input=None):
    """
    Recherche un Pokémon par numéro, nom FR ou nom EN.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Préparation de la forme (mapping)
            forme_map = {
                'alola': 'A', 'alolan': 'A', 'a': 'A',
                'galar': 'G', 'galarian': 'G', 'g': 'G',
                'hisui': 'H', 'hisuian': 'H', 'h': 'H',
                'paldea': 'P', 'paldean': 'P', 'p': 'P'
            }
            forme_code = forme_map.get(forme_input.lower()) if forme_input else ""

            # 2. Préparation de l'ID si c'est un nombre
            search_id = None
            if query_text.isdigit():
                search_id = query_text.zfill(4)

            # 3. Requête SQL flexible (insensible à la casse par défaut en MySQL)
            # Pour les accents, MySQL avec une collation utf8mb4_unicode_ci ignore déjà les accents.
            sql = """
                SELECT * FROM scpk_pokemon 
                WHERE (num_dex = %s OR nom_fr = %s OR nom_en = %s)
                AND (forme = %s OR (%s = '' AND (forme IS NULL OR forme = '')))
                LIMIT 1
            """
            cursor.execute(sql, (search_id, query_text, query_text, forme_code, forme_code))
            return cursor.fetchone()
    finally:
        conn.close()