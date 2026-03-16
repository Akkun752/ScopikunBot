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
    
def set_friend_code(user_id, friend_code):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # On utilise ON DUPLICATE KEY UPDATE pour mettre à jour si l'ID existe déjà
            sql = "INSERT INTO saft_profiles (user_id, friend_code) VALUES (%s, %s) ON DUPLICATE KEY UPDATE friend_code = %s"
            cursor.execute(sql, (user_id, friend_code, friend_code))
        conn.commit()
    finally:
        conn.close()

def get_friend_code(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT friend_code FROM saft_profiles WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            return result['friend_code'] if result else None
    finally:
        conn.close()

def get_profile(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM saft_profiles WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def update_profile_value(user_id, column, value):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Ensure profile exists
            cursor.execute("INSERT IGNORE INTO saft_profiles (user_id) VALUES (%s)", (user_id,))
            # Update specific column
            sql = f"UPDATE saft_profiles SET {column} = %s WHERE user_id = %s"
            cursor.execute(sql, (value, user_id))
            conn.commit()
    finally:
        conn.close()

def validate_pokemon_id(query):
    """Vérifie si le pokémon existe et retourne son ID unique (pk)."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            search_id = query.zfill(4) if query.isdigit() else None
            sql = "SELECT id FROM scpk_pokemon WHERE num_dex = %s OR nom_fr = %s OR nom_en = %s LIMIT 1"
            cursor.execute(sql, (search_id, query, query))
            result = cursor.fetchone()
            return result['id'] if result else None
    finally:
        conn.close()

def get_profile_with_pokemon(user_id):
    """Récupère le profil et joint le nom du pokémon via son ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT p.*, s.nom_en as pokemon_name 
                FROM saft_profiles p
                LEFT JOIN scpk_pokemon s ON p.fav_pokemon = s.id
                WHERE p.user_id = %s
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()