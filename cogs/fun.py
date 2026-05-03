import discord
from discord import app_commands
from discord.ext import commands
import random
import aiohttp

BLAGUES = [
    "Pourquoi les plongeurs plongent-ils toujours en arrière ? Parce que sinon ils tomberaient dans le bateau !",
    "Qu'est-ce qu'un canif ? Un petit fien.",
    "Pourquoi le scarabée est-il l'insecte préféré des informaticiens ? Parce que c'est un bug.",
    "C'est l'histoire d'un homme qui rentre dans une bibliothèque et dit : 'Un steak haché et des frites !' La bibliothécaire répond : 'Monsieur, ici c'est une bibliothèque !' L'homme chuchote : 'Pardon... un steak haché et des frites.'",
    "Qu'est-ce qu'un crocodile qui surveille la cour d'école ? Un sac à dents.",
    "Pourquoi les français mangent-ils des escargots ? Parce qu'ils n'aiment pas la fast-food.",
    "Comment appelle-t-on un chat tombé dans un pot de peinture ? Un chat-peint.",
    "Quelle est la différence entre un crocodile ? Plus c'est vert, plus c'est jaune.",
]

REPONSES_8BALL = [
    "✅ Oui, absolument !",
    "✅ C'est certain.",
    "✅ Sans aucun doute.",
    "✅ Tu peux compter dessus.",
    "🤔 C'est probable.",
    "🤔 Les signes indiquent que oui.",
    "🤔 Demande encore plus tard.",
    "🤔 Je ne peux pas te répondre maintenant.",
    "❌ Ne compte pas là-dessus.",
    "❌ Ma réponse est non.",
    "❌ Mes sources disent non.",
    "❌ Les perspectives ne sont pas bonnes.",
]

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /8ball ────────────────────────────────────────────────────────────
    @app_commands.command(name="8ball", description="Pose une question à la boule magique")
    @app_commands.describe(question="Ta question")
    async def ball(self, interaction: discord.Interaction, question: str):
        reponse = random.choice(REPONSES_8BALL)
        embed = discord.Embed(title="🎱 Boule Magique", color=discord.Color.purple())
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="💬 Réponse", value=reponse, inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /pile ─────────────────────────────────────────────────────────────
    @app_commands.command(name="pile", description="Pile ou face ?")
    async def pile(self, interaction: discord.Interaction):
        resultat = random.choice(["🪙 **Pile !**", "🪙 **Face !**"])
        await interaction.response.send_message(resultat)

    # ── /de ───────────────────────────────────────────────────────────────
    @app_commands.command(name="de", description="Lancer un dé")
    @app_commands.describe(faces="Nombre de faces du dé (6 par défaut)")
    async def de(self, interaction: discord.Interaction, faces: int = 6):
        if faces < 2:
            await interaction.response.send_message("❌ Le dé doit avoir au moins 2 faces.", ephemeral=True)
            return
        resultat = random.randint(1, faces)
        embed = discord.Embed(
            title="🎲 Lancer de dé",
            description=f"Dé à **{faces}** faces → **{resultat}**",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    # ── /blague ───────────────────────────────────────────────────────────
    @app_commands.command(name="blague", description="Une blague aléatoire")
    async def blague(self, interaction: discord.Interaction):
        blague = random.choice(BLAGUES)
        embed = discord.Embed(
            title="😂 Blague du jour",
            description=blague,
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)

    # ── /chiffre ──────────────────────────────────────────────────────────
    @app_commands.command(name="chiffre", description="Devine un nombre entre 1 et 100")
    async def chiffre(self, interaction: discord.Interaction):
        nombre = random.randint(1, 100)
        embed = discord.Embed(
            title="🔢 Nombre aléatoire",
            description=f"Le nombre tiré est : **{nombre}**",
            color=discord.Color.teal()
        )
        await interaction.response.send_message(embed=embed)

    # ── /rps ──────────────────────────────────────────────────────────────
    @app_commands.command(name="rps", description="Pierre, feuille, ciseaux !")
    @app_commands.describe(choix="Ton choix")
    @app_commands.choices(choix=[
        app_commands.Choice(name="Pierre 🪨", value="pierre"),
        app_commands.Choice(name="Feuille 📄", value="feuille"),
        app_commands.Choice(name="Ciseaux ✂️", value="ciseaux"),
    ])
    async def rps(self, interaction: discord.Interaction, choix: app_commands.Choice[str]):
        options = ["pierre", "feuille", "ciseaux"]
        emojis = {"pierre": "🪨", "feuille": "📄", "ciseaux": "✂️"}
        bot_choix = random.choice(options)

        gagne = {
            "pierre": "ciseaux",
            "feuille": "pierre",
            "ciseaux": "feuille"
        }

        if choix.value == bot_choix:
            resultat = "🤝 Égalité !"
            couleur = discord.Color.yellow()
        elif gagne[choix.value] == bot_choix:
            resultat = "🎉 Tu as gagné !"
            couleur = discord.Color.green()
        else:
            resultat = "💀 Tu as perdu !"
            couleur = discord.Color.red()

        embed = discord.Embed(title="✊ Pierre Feuille Ciseaux", color=couleur)
        embed.add_field(name="Ton choix", value=emojis[choix.value], inline=True)
        embed.add_field(name="Mon choix", value=emojis[bot_choix], inline=True)
        embed.add_field(name="Résultat", value=resultat, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
