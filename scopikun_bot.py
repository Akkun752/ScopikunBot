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
VERSION = "v0.0.3"
print(f"Lancement du bot Scopikun {VERSION}...")

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
@bot.tree.command(name="help", description="Affiche toutes les commandes du bot")
async def help_command(interaction: discord.Interaction): # Retrait de self
    embed = discord.Embed(
        title="Centre d'aide de Scopikun",
        description="Voici la liste des commandes disponibles avec Scopikun !",
        color=discord.Color.red()
    )
    embed.add_field(name="/pokedex", value="Affiche la page Pokédex d'un Pokémon", inline=False)

    if interaction.user.guild_permissions.administrator:
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="**Commandes Administrateurs**", inline=False)
    await interaction.response.send_message(embed=embed)

# === Commande /pokedex ===
@bot.tree.command(name="pokedex", description="Affiche les informations d'un Pokémon")
@app_commands.describe(
    pokemon="Nom (FR/EN) ou numéro du Pokémon",
    forme="Optionnel : Alola, Galar, Hisui, Paldea (ou A, G, H, P)"
)
async def pokedex(interaction: discord.Interaction, pokemon: str, forme: str = None):
    # recup db
    data = scopikun_db.get_pokemon_data(pokemon, forme)
    if not data:
        await interaction.response.send_message(
            f"❌ Impossible de trouver le Pokémon **{pokemon}**" + 
            (f" sous la forme **{forme}**." if forme else "."), 
            ephemeral=True
        )
        return

    # image
    num = str(data['num_dex']).zfill(4)
    code_forme = data['forme'] if data['forme'] else ""
    filename = f"{num}{code_forme}.png"
    path_image = f"./sprites/{filename}"
    if not os.path.exists(path_image):
        await interaction.response.send_message(f"❌ Image locale manquante : `{filename}`", ephemeral=True)
        return
    file = discord.File(path_image, filename="pokemon.png")

    # embed
    embed = discord.Embed(
        title=f"#{num} - {data['nom_fr']}",
        description=data['description'],
        color=discord.Color.red()
    )
    embed.set_thumbnail(url="attachment://pokemon.png")
    type_str = data['type_1'] + (f" / {data['type_2']}" if data['type_2'] else "")
    embed.add_field(name="Types", value=type_str, inline=True)
    embed.add_field(name="Nom Anglais", value=data['nom_en'], inline=True)

    if data['forme']:
        if data['forme'] == "A":
            formname = "Alola"
        elif data['forme'] == "G":
            formname = "Galar"
        elif data['forme'] == "H":
            formname = "Hisui"
        elif data['forme'] == "P":
            formname = "Paldea"
        else:
            formname = data['forme']
        embed.add_field(name="Forme", value=formname, inline=True)
    stats = (
        f"**PV:** {data['hp']}\n"
        f"**ATK:** {data['atk']}\n"
        f"**DEF:** {data['def']}\n"
        f"**SPA:** {data['spa']}\n"
        f"**SPD:** {data['spd']}\n"
        f"**SPE:** {data['spe']}"
    )
    embed.add_field(name="Statistiques de base", value=stats, inline=False)

    await interaction.response.send_message(embed=embed, file=file)
    
# === Lancer le bot ===
bot.run(os.getenv("DISCORD_TOKEN"))
