import discord
import os
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
import feedparser
import aiohttp
import random
import aiohttp
import io
from PIL import Image

import scopikun_db

load_dotenv()

# Configuration
VERSION = "v0.0.7"
print(f"Lancement du bot SAF Team {VERSION}...")

TYPE_TRANSLATIONS = {
    "Feu": "Fire",
    "Eau": "Water",
    "Plante": "Grass",
    "Électrik": "Electric",
    "Normal": "Normal",
    "Spectre": "Ghost",
    "Acier": "Steel",
    "Poison": "Poison",
    "Insecte": "Bug",
    "Combat": "Fighting",
    "Vol": "Flying",
    "Dragon": "Dragon",
    "Ténèbres": "Dark",
    "Fée": "Fairy",
    "Glace": "Ice",
    "Roche": "Rock",
    "Sol": "Ground",
    "Psy": "Psychic",
}

class MyBot(commands.Bot):
    def __init__(self):
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name=f"🎒 /help | {VERSION}"
        )
        super().__init__(
            command_prefix="!", 
            intents=discord.Intents.all(), 
            activity=activity
        )

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

# === Événement au démarrage ===
@bot.event
async def on_ready():
    print(f"Bot en route ! Connecté sur {len(bot.guilds)} serveurs.")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur de synchronisation : {e}")

# === Commande /help ===
@bot.tree.command(name="help", description="Display all the Bot's commands")
async def help_command(interaction: discord.Interaction): # Retrait de self
    embed = discord.Embed(
        title="SAFT Bot Help Center",
        description="Here are all the commands !",
        color=discord.Color(0x8A2BE2)
    )
    embed.add_field(name="/pokedex", value="Display the Pokédex page of a Pokémon", inline=False)

    if interaction.user.guild_permissions.administrator:
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="**Admin Commands**", inline=False)
    await interaction.response.send_message(embed=embed)

# === Commande /pokedex ===
@bot.tree.command(name="pokedex", description="Display the Pokédex page of a Pokémon")
@app_commands.describe(
    pokemon="Name (EN/FR) or Dex Number",
    forme="Optionnal : Alola, Galar, Hisui, Paldea (or A, G, H, P)"
)
async def pokedex(interaction: discord.Interaction, pokemon: str, forme: str = None):
    # recup db
    data = scopikun_db.get_pokemon_data(pokemon, forme)
    if not data:
        await interaction.response.send_message(
            f"❌ Impossible to find the Pokémon **{pokemon}**" + 
            (f" with form : **{forme}**." if forme else "."), 
            ephemeral=True
        )
        return

    # image
# 1. Récupération du numéro (ex: 0019 ou 0983)
    num = str(data['num_dex']).zfill(4)
    
    # 2. Logique du suffixe
    # On n'ajoute un suffixe QUE si ce n'est PAS la forme originale du Pokémon.
    # Dans ta DB, les formes originales ont souvent l'ID le plus bas pour un num_dex.
    
    suffixe = ""
    region = data.get('region')
    if region == "Unys":
            region = "Unova"
    
    # Liste des régions qui DOIVENT avoir un suffixe (les formes régionales)
    # On vérifie si le nom contient la région ou si c'est une exception connue
    # Mais le plus simple : est-ce que c'est un Rattata d'Alola ou un Scalpereur natif ?
    
    # On regarde si la colonne 'forme' en DB contient un code (A, G, H, P)
    # ou si la région est une région de "forme" ET que le Pokémon existe ailleurs.
    
    if data.get('forme') in ['A', 'G', 'H', 'P']:
        suffixe = data['forme']
    elif region == "Alola" and int(num) < 722: # Pokémon des anciennes gen en version Alola
        suffixe = "A"
    elif region == "Galar" and int(num) < 810: # Pokémon des anciennes gen en version Galar
        suffixe = "G"
    elif region == "Hisui" and int(num) < 899: # Pokémon des anciennes gen en version Hisui
        suffixe = "H"
    elif region == "Paldea" and int(num) < 906: # Pokémon des anciennes gen en version Paldea (ex: Tauros)
        suffixe = "P"

    # 3. Construction du nom de fichier
    filename = f"{num}{suffixe}.png"
    path_image = f"./sprites/{filename}"
    
    if not os.path.exists(path_image):
        await interaction.response.send_message(f"❌ Image not found : `{filename}`", ephemeral=True)
        return
    file = discord.File(path_image, filename="pokemon.png")

    # embed
    embed = discord.Embed(
        title=f"#{num} - {data['nom_en']}",
        #description=data['description'],
        color=discord.Color(0x8A2BE2)
    )
    embed.set_thumbnail(url="attachment://pokemon.png")
    type_1 = TYPE_TRANSLATIONS.get(data['type_1'], data['type_1'])  # On garde le type en français si non trouvé
    type_2 = TYPE_TRANSLATIONS.get(data['type_2'], data['type_2']) if data['type_2'] else None
    type_str = type_1 + (f" / {type_2}" if type_2 else "")
    embed.add_field(name="Types", value=type_str, inline=True)
    embed.add_field(name="French Name", value=data['nom_fr'], inline=True)

    if data.get('region'):
        # On affiche directement ce qu'il y a en base de données
        embed.add_field(name="Region", value=data['region'], inline=True)
    stats = (
        f"**PV:** {data['hp']}\n"
        f"**ATK:** {data['atk']}\n"
        f"**DEF:** {data['def']}\n"
        f"**SPA:** {data['spa']}\n"
        f"**SPD:** {data['spd']}\n"
        f"**SPE:** {data['spe']}"
    )
    embed.add_field(name="Statistics", value=stats, inline=False)

    await interaction.response.send_message(embed=embed, file=file)
    
# === Lancer le bot ===
bot.run(os.getenv("DISCORD_TOKEN"))
