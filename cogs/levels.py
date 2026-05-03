import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import asyncio

XP_FILE = "xp_data.json"
XP_MIN = 5
XP_MAX = 15
XP_COOLDOWN = 60  # secondes entre deux gains d'XP

def load_xp() -> dict:
    if os.path.exists(XP_FILE):
        with open(XP_FILE, "r") as f:
            return json.load(f)
    return {}

def save_xp(data: dict):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def xp_for_level(level: int) -> int:
    """XP nécessaire pour atteindre le niveau suivant."""
    return 100 * (level ** 2) + 50 * level

def get_level(xp: int) -> int:
    level = 0
    while xp >= xp_for_level(level + 1):
        level += 1
    return level

class Levels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.xp_data = load_xp()
        self.cooldowns: dict[str, float] = {}  # "guild_id:user_id" -> timestamp

    def get_user_data(self, guild_id: int, user_id: int) -> dict:
        key = f"{guild_id}"
        if key not in self.xp_data:
            self.xp_data[key] = {}
        uid = str(user_id)
        if uid not in self.xp_data[key]:
            self.xp_data[key][uid] = {"xp": 0, "level": 0}
        return self.xp_data[key][uid]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        cooldown_key = f"{message.guild.id}:{message.author.id}"
        now = asyncio.get_event_loop().time()

        # Anti-spam XP
        if cooldown_key in self.cooldowns:
            if now - self.cooldowns[cooldown_key] < XP_COOLDOWN:
                return

        self.cooldowns[cooldown_key] = now
        data = self.get_user_data(message.guild.id, message.author.id)
        old_level = data["level"]

        # Ajout XP
        gain = random.randint(XP_MIN, XP_MAX)
        data["xp"] += gain
        data["level"] = get_level(data["xp"])
        save_xp(self.xp_data)

        # Level up !
        if data["level"] > old_level:
            embed = discord.Embed(
                title="⬆️ Level Up !",
                description=f"{message.author.mention} est passé au niveau **{data['level']}** ! 🎉",
                color=discord.Color.gold()
            )
            await message.channel.send(embed=embed)

    # ── /rank ─────────────────────────────────────────────────────────────
    @app_commands.command(name="rank", description="Voir ton niveau et ton XP")
    @app_commands.describe(membre="Le membre à inspecter (toi par défaut)")
    async def rank(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        data = self.get_user_data(interaction.guild_id, membre.id)
        level = data["level"]
        xp = data["xp"]
        xp_needed = xp_for_level(level + 1)
        xp_current_level = xp_for_level(level)
        xp_progress = xp - xp_current_level
        xp_required = xp_needed - xp_current_level

        # Barre de progression
        filled = int((xp_progress / xp_required) * 20) if xp_required > 0 else 20
        bar = "█" * filled + "░" * (20 - filled)

        embed = discord.Embed(
            title=f"⭐ Niveau de {membre.display_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="🏆 Niveau", value=str(level), inline=True)
        embed.add_field(name="✨ XP Total", value=str(xp), inline=True)
        embed.add_field(
            name=f"📊 Progression vers niveau {level + 1}",
            value=f"`{bar}` {xp_progress}/{xp_required} XP",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    # ── /leaderboard ──────────────────────────────────────────────────────
    @app_commands.command(name="leaderboard", description="Classement XP du serveur")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_data = self.xp_data.get(str(interaction.guild_id), {})
        if not guild_data:
            await interaction.response.send_message("❌ Aucune donnée XP pour ce serveur.", ephemeral=True)
            return

        sorted_users = sorted(guild_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

        embed = discord.Embed(title="🏆 Classement XP", color=discord.Color.gold())
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, udata) in enumerate(sorted_users):
            medal = medals[i] if i < 3 else f"`{i+1}.`"
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"Utilisateur #{uid}"
            lines.append(f"{medal} **{name}** — Niveau {udata['level']} ({udata['xp']} XP)")

        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)

    # ── /xp-add (admin) ───────────────────────────────────────────────────
    @app_commands.command(name="xp-add", description="Ajouter de l'XP à un membre (admin)")
    @app_commands.describe(membre="Le membre", quantite="Quantité d'XP à ajouter")
    @app_commands.checks.has_permissions(administrator=True)
    async def xp_add(self, interaction: discord.Interaction, membre: discord.Member, quantite: int):
        data = self.get_user_data(interaction.guild_id, membre.id)
        data["xp"] += quantite
        data["level"] = get_level(data["xp"])
        save_xp(self.xp_data)
        await interaction.response.send_message(
            f"✅ **{quantite} XP** ajoutés à {membre.mention}. Total : **{data['xp']} XP** (Niveau {data['level']})"
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
