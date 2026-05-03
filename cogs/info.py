import discord
from discord import app_commands
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /userinfo ─────────────────────────────────────────────────────────
    @app_commands.command(name="userinfo", description="Afficher les infos d'un membre")
    @app_commands.describe(membre="Le membre à inspecter (toi par défaut)")
    async def userinfo(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user

        roles = [r.mention for r in membre.roles if r.name != "@everyone"]
        roles_str = ", ".join(roles) if roles else "Aucun"

        embed = discord.Embed(
            title=f"👤 Infos — {membre}",
            color=membre.color if membre.color != discord.Color.default() else discord.Color.blurple()
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="🆔 ID", value=membre.id, inline=True)
        embed.add_field(name="🏷️ Pseudo", value=membre.display_name, inline=True)
        embed.add_field(name="🤖 Bot", value="Oui" if membre.bot else "Non", inline=True)
        embed.add_field(
            name="📅 Compte créé le",
            value=discord.utils.format_dt(membre.created_at, style="D"),
            inline=True
        )
        embed.add_field(
            name="📥 A rejoint le",
            value=discord.utils.format_dt(membre.joined_at, style="D"),
            inline=True
        )
        embed.add_field(name=f"🎭 Rôles ({len(roles)})", value=roles_str[:1024], inline=False)

        if membre.premium_since:
            embed.add_field(
                name="💎 Boost depuis",
                value=discord.utils.format_dt(membre.premium_since, style="D"),
                inline=True
            )

        await interaction.response.send_message(embed=embed)

    # ── /serverinfo ───────────────────────────────────────────────────────
    @app_commands.command(name="serverinfo", description="Afficher les infos du serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(
            title=f"🏠 {guild.name}",
            color=discord.Color.blurple()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="👑 Propriétaire", value=guild.owner.mention if guild.owner else "Inconnu", inline=True)
        embed.add_field(
            name="📅 Créé le",
            value=discord.utils.format_dt(guild.created_at, style="D"),
            inline=True
        )
        embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Salons texte", value=len(guild.text_channels), inline=True)
        embed.add_field(name="🔊 Salons vocaux", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="📁 Catégories", value=len(guild.categories), inline=True)
        embed.add_field(name="🎭 Rôles", value=len(guild.roles), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(
            name="💎 Boosts",
            value=f"{guild.premium_subscription_count} (Niveau {guild.premium_tier})",
            inline=True
        )
        embed.add_field(name="🔒 Vérification", value=str(guild.verification_level).capitalize(), inline=True)

        await interaction.response.send_message(embed=embed)

    # ── /avatar ───────────────────────────────────────────────────────────
    @app_commands.command(name="avatar", description="Afficher l'avatar d'un membre")
    @app_commands.describe(membre="Le membre dont voir l'avatar (toi par défaut)")
    async def avatar(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar de {membre.display_name}", color=discord.Color.blurple())
        embed.set_image(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # ── /ping ─────────────────────────────────────────────────────────────
    @app_commands.command(name="ping", description="Afficher la latence du bot")
    async def ping(self, interaction: discord.Interaction):
        latence = round(self.bot.latency * 1000)
        couleur = discord.Color.green() if latence < 100 else discord.Color.orange() if latence < 200 else discord.Color.red()
        embed = discord.Embed(
            title="🏓 Pong !",
            description=f"Latence : **{latence}ms**",
            color=couleur
        )
        await interaction.response.send_message(embed=embed)

    # ── /stats ────────────────────────────────────────────────────────────
    @app_commands.command(name="stats", description="Statistiques globales du bot")
    async def stats(self, interaction: discord.Interaction):
        total_membres = sum(g.member_count for g in self.bot.guilds)
        embed = discord.Embed(title="📊 Statistiques du bot", color=discord.Color.blurple())
        embed.add_field(name="🏠 Serveurs", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="👥 Membres totaux", value=total_membres, inline=True)
        embed.add_field(name="🏓 Latence", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.set_footer(text=f"Bot : {self.bot.user}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
