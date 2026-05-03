import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import random
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Vérifier la configuration voix
try:
    import davey
    print("✅ davey chargé")
except ModuleNotFoundError:
    print("⚠️ davey non installé : installez-le avec `pip install davey` pour utiliser la voix Discord.")

if not discord.opus.is_loaded():
    print("⚠️ Opus non chargé : installez libopus et vérifiez que PyNaCl est bien activé.")
else:
    print("✅ Opus chargé")

COGS = [
    "cogs.moderation",
    "cogs.info",
    "cogs.fun",
    "cogs.music",
    "cogs.giveaway",
    "cogs.tickets",
    "cogs.levels",
    "cogs.vocal_prive",
    "cogs.autoroles",
]

CLASHS = [
    "{target.mention} est tellement nul qu'il ferait perdre une IA à Pierre-Papier-Ciseaux",
    "{target.mention} a le QI d'une huître... et encore, l'huître est vexée",
    "Si {target.mention} était un pokémon, ce serait un Magicarpe niveau 1",
    "{target.mention} est la raison pour laquelle y'a des instructions sur les shampoings",
    "{target.mention} a déjà perdu une bataille de regards contre un poisson rouge",
    "Le Wi-Fi se déconnecte quand {target.mention} entre dans la pièce",
    "{target.mention} est comme Internet Explorer : lent et personne ne l'utilise",
    "Si la médiocrité était un art, {target.mention} serait Picasso",
]

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot connecté : {bot.user}")
    print(f"✅ {len(bot.cogs)} cogs chargés")
    print("✅ Slash commands synchronisées")

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"  ✅ {cog}")
        except Exception as e:
            print(f"  ❌ {cog} : {e}")

@bot.tree.command(name="clash", description="Envoie un clash à un membre 😈")
@app_commands.describe(membre="Le membre à clasher")
async def clash(interaction: discord.Interaction, membre: discord.Member):
    phrase = random.choice(CLASHS)
    
    if "{target.mention}" in phrase:
        phrase = phrase.format(target=membre)

    embed = discord.Embed(
        description=f">>> {phrase}",
        color=0xFF0000
    )
    embed.set_author(
        name=f"{interaction.user.display_name} t'envoie un clash 😈",
        icon_url=interaction.user.display_avatar.url
    )
    embed.set_footer(text="C'est pour rire hein 😅")

    await interaction.response.send_message(
        content=membre.mention,
        embed=embed
    )

async def main():
    print("Chargement des cogs...")
    await load_cogs()
    await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())