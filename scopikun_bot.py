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
VERSION = "v0.1.1"
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
    embed.add_field(name="/fiend_code", value="Show your Nintendo Friend Code", inline=False)
    embed.add_field(name="/pokedex", value="Display the Pokédex page of a Pokémon", inline=False)
    embed.add_field(name="/set_fiend_code", value="Set your Nintendo Friend Code", inline=False)

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

    num = str(data['num_dex']).zfill(4)
    
    suffixe = ""
    region = data.get('region')
    if region == "Unys":
            region = "Unova"
    
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

    filename = f"{num}{suffixe}.png"
    path_image = f"./sprites/{filename}"
    
    if not os.path.exists(path_image):
        await interaction.response.send_message(f"❌ Image not found : `{filename}`", ephemeral=True)
        return
    file = discord.File(path_image, filename="pokemon.png")

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
        embed.add_field(name="Region", value=region, inline=True)
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

# === Commande /friend_code_set ===
@bot.tree.command(name="set_friend_code", description="Set your Nintendo Friend Code")
@app_commands.describe(code="Your Friend Code (ex: SW-1234-5678-9012)")
async def fc_set(interaction: discord.Interaction, code: str):
    scopikun_db.set_friend_code(interaction.user.id, code)
    await interaction.response.send_message(f"✅ Friend Code set : `{code}`", ephemeral=True)

# === Commande /friend_code ===
@bot.tree.command(name="friend_code", description="Show your Nintendo Friend Code")
async def fc_get(interaction: discord.Interaction):
    code = scopikun_db.get_friend_code(interaction.user.id)
    
    if not code:
        await interaction.response.send_message(
            "❌ You did not set your Friend Code. Use `/friend_code_set`.", 
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"Nintendo Switch FC : {interaction.user.display_name}",
        description=f"**{code}**",
        color=discord.Color(0x8A2BE2)
    )
    
    if interaction.user.avatar:
        embed.set_thumbnail(url=interaction.user.avatar.url)
    else:
        embed.set_thumbnail(url=interaction.user.default_avatar.url)

    await interaction.response.send_message(embed=embed)

# === Profile Settings Commands ===

@bot.tree.command(name="set_favourite_pokemon", description="Set your favourite Pokémon")
@app_commands.describe(pokemon="Name (EN/FR) or Dex Number")
async def set_fav_pokemon(interaction: discord.Interaction, pokemon: str):
    # Correction : on récupère l'ID et non le nom
    pk_id = scopikun_db.validate_pokemon_id(pokemon)
    
    if not pk_id:
        await interaction.response.send_message(f"❌ Pokémon **{pokemon}** not found in the Pokédex.", ephemeral=True)
        return

    # On enregistre l'ID en base
    scopikun_db.update_profile_value(interaction.user.id, "fav_pokemon", pk_id)
    await interaction.response.send_message(f"✅ Your favourite Pokémon has been updated!", ephemeral=True)

@bot.tree.command(name="set_favourite_game", description="Select your favourite Pokémon game")
@app_commands.describe(game="Choose a game from the list")
@app_commands.choices(game=[
    app_commands.Choice(name="Red, Blue & Yellow", value="Pokémon Red, Blue & Yellow"),
    app_commands.Choice(name="Gold, Silver & Crystal", value="Pokémon Gold, Silver & Crystal"),
    app_commands.Choice(name="Ruby, Sapphire & Emerald", value="Pokémon Ruby, Sapphire & Emerald"),
    app_commands.Choice(name="Fire Red & Leaf Green", value="Pokémon Fire Red & Leaf Green"),
    app_commands.Choice(name="Diamond, Pearl & Platinum", value="Pokémon Diamond, Pearl & Platinum"),
    app_commands.Choice(name="HeartGold & SoulSilver", value="Pokémon HeartGold & SoulSilver"),
    app_commands.Choice(name="Black & White", value="Pokémon Black & White"),
    app_commands.Choice(name="Black 2 & White 2", value="Pokémon Black 2 & White 2"),
    app_commands.Choice(name="X & Y", value="Pokémon X & Y"),
    app_commands.Choice(name="Omega Ruby & Alpha Sapphire", value="Pokémon Omega Ruby & Alpha Sapphire"),
    app_commands.Choice(name="Sun & Moon", value="Pokémon Sun & Moon"),
    app_commands.Choice(name="Ultra-Sun & Ultra-Moon", value="Pokémon Ultra-Sun & Ultra-Moon"),
    app_commands.Choice(name="Sword & Shield", value="Pokémon Sword & Shield"),
    app_commands.Choice(name="Brilliant Diamond & Shining Pearl", value="Pokémon Brilliant Diamond & Shining Pearl"),
    app_commands.Choice(name="Legends: Arceus", value="Pokémon Legends: Arceus"),
    app_commands.Choice(name="Scarlet & Violet", value="Pokémon Scarlet & Violet"),
    app_commands.Choice(name="Legends: Z-A", value="Pokémon Legends: Z-A"),
])
async def set_fav_game(interaction: discord.Interaction, game: app_commands.Choice[str]):
    scopikun_db.update_profile_value(interaction.user.id, "fav_game", game.value)
    await interaction.response.send_message(f"✅ Your favourite game is now set to: **{game.name}**", ephemeral=True)

# === Main Profile Command ===

@bot.tree.command(name="profile", description="Display a trainer profile")
@app_commands.describe(member="Select a member to view their profile")
async def profile(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    
    # Correction : On utilise la fonction avec jointure pour avoir le nom du Pokémon
    data = scopikun_db.get_profile_with_pokemon(target.id)

    # Création du profil s'il n'existe pas
    if not data:
        scopikun_db.update_profile_value(target.id, "user_id", target.id)
        data = scopikun_db.get_profile_with_pokemon(target.id)

    embed = discord.Embed(
        title=f"{target.display_name}'s Profile",
        color=discord.Color(0x8A2BE2)
    )
    
    avatar_url = target.avatar.url if target.avatar else target.default_avatar.url
    embed.set_thumbnail(url=avatar_url)

    # Récupération du nom du pokémon (ou 'Unknown' s'il n'y en a pas)
    fav_pk_name = data.get('pokemon_name') or "Unknown"

    embed.add_field(name="🎮 Friend Code", value=f"`{data['friend_code']}`", inline=False)
    embed.add_field(name="⭐ Fav. Pokémon", value=fav_pk_name, inline=True)
    embed.add_field(name="💿 Fav. Game", value=data['fav_game'], inline=True)
    
    stats = (
        f"🎫 Participations: **{data['participations']}**\n"
        f"🏆 Victories: **{data['victories']}**"
    )
    embed.add_field(name="📊 SAF Stats", value=stats, inline=False)

    await interaction.response.send_message(embed=embed)
    
# === Lancer le bot ===
bot.run(os.getenv("DISCORD_TOKEN"))
