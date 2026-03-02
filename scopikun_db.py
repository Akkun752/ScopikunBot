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

def get_pokemon_data(query_text, region_input=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Mapping enrichi avec les abréviations courantes
            region_map = {
                'kanto': 'Kanto',
                'johto': 'Johto',
                'hoenn': 'Hoenn',
                'sinnoh': 'Sinnoh',
                'unys': 'Unys',
                'kalos': 'Kalos',
                'alola': 'Alola', 'alolan': 'Alola', 'a': 'Alola',
                'galar': 'Galar', 'galarian': 'Galar', 'g': 'Galar',
                'hisui': 'Hisui', 'hisuian': 'Hisui', 'h': 'Hisui',
                'paldea': 'Paldea', 'paldean': 'Paldea', 'p': 'Paldea'
            }
            
            target_region = None
            if region_input:
                target_region = region_map.get(region_input.lower())

            search_id = None
            if query_text.isdigit():
                search_id = query_text.zfill(4)

            # 2. Construction de la requête
            sql = "SELECT * FROM scpk_pokemon WHERE (num_dex = %s OR nom_fr = %s OR nom_en = %s)"
            params = [search_id, query_text, query_text]

            if target_region:
                sql += " AND region = %s"
                params.append(target_region)
            else:
                # Priorité à l'ID le plus bas (Kanto) si rien n'est précisé
                sql += " ORDER BY id ASC LIMIT 1"

            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        conn.close()