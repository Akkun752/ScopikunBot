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

import scopikun_db

load_dotenv()

# Configuration
VERSION = "v0.0.1"
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
    embed.add_field(name="/akkun", value="Affiche les chaînes Akkun7", inline=False)
    embed.add_field(name="/panel", value="Affiche les liens d'Astero", inline=False)

    if interaction.user.guild_permissions.administrator:
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="**Commandes Administrateurs**", inline=False)
    await interaction.response.send_message(embed=embed)

# === Commande /akkun ===
@bot.tree.command(name="akkun", description="Affiche les chaînes Akkun7")
async def akkun(interaction: discord.Interaction): # Retrait de self
    embed = discord.Embed(title="Akkun", description="**Voici les chaînes de Akkun :**", color=discord.Color.red())
    embed.set_thumbnail(url="https://www.akkunverse.fr/scopikun/akkun.png")
    embed.add_field(name="🎥 YouTube", value="https://youtube.com/@Akkun7", inline=False)
    embed.add_field(name="🎬 YouTube VOD", value="https://youtube.com/@Akkun7VOD", inline=False)
    embed.add_field(name="👾 Twitch", value="https://twitch.tv/akkun752", inline=False)
    embed.add_field(name="🤖 Discord", value="https://discord.gg/24kM8KUd9j", inline=False)
    await interaction.response.send_message(embed=embed)

# === Commande /panel ===
@bot.tree.command(name="panel", description="Affiche les liens de Scopikun")
async def panel(interaction: discord.Interaction): # Retrait de self
    embed = discord.Embed(title="Scopikun", description="**Voici les différents liens de Scopikun :**", color=discord.Color.red())
    embed.set_thumbnail(url="https://www.akkunverse.fr/scopikun/ScopikunBot.png")
    embed.add_field(name="🤖 Discord", value="``- À venir -``", inline=False)
    embed.add_field(name="🌐 Site web", value="``- À venir -``", inline=False)
    await interaction.response.send_message(embed=embed)

# === Lancer le bot ===
bot.run(os.getenv("DISCORD_TOKEN"))
