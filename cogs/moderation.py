import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── /ban ──────────────────────────────────────────────────────────────
    @app_commands.command(name="ban", description="Bannir un membre du serveur")
    @app_commands.describe(membre="Le membre à bannir", raison="Raison du ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        if membre.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Tu ne peux pas bannir quelqu'un avec un rôle égal ou supérieur au tien.", ephemeral=True)
            return
        try:
            await membre.send(f"🔨 Tu as été **banni** de **{interaction.guild.name}**.\nRaison : {raison}")
        except discord.Forbidden:
            pass
        await membre.ban(reason=raison)
        await interaction.response.send_message(f"🔨 **{membre}** a été banni.\nRaison : {raison}")

    # ── /kick ─────────────────────────────────────────────────────────────
    @app_commands.command(name="kick", description="Expulser un membre du serveur")
    @app_commands.describe(membre="Le membre à expulser", raison="Raison du kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison fournie"):
        if membre.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Tu ne peux pas expulser quelqu'un avec un rôle égal ou supérieur au tien.", ephemeral=True)
            return
        try:
            await membre.send(f"👢 Tu as été **expulsé** de **{interaction.guild.name}**.\nRaison : {raison}")
        except discord.Forbidden:
            pass
        await membre.kick(reason=raison)
        await interaction.response.send_message(f"👢 **{membre}** a été expulsé.\nRaison : {raison}")

    # ── /mute ─────────────────────────────────────────────────────────────
    @app_commands.command(name="mute", description="Rendre muet un membre (timeout)")
    @app_commands.describe(membre="Le membre à mute", duree="Durée en minutes", raison="Raison")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membre: discord.Member, duree: int = 10, raison: str = "Aucune raison fournie"):
        if membre.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ Tu ne peux pas mute quelqu'un avec un rôle égal ou supérieur au tien.", ephemeral=True)
            return
        until = discord.utils.utcnow() + timedelta(minutes=duree)
        await membre.timeout(until, reason=raison)
        await interaction.response.send_message(f"🔇 **{membre}** a été mute pendant **{duree} minutes**.\nRaison : {raison}")

    # ── /unmute ───────────────────────────────────────────────────────────
    @app_commands.command(name="unmute", description="Retirer le mute d'un membre")
    @app_commands.describe(membre="Le membre à unmute")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.timeout(None)
        await interaction.response.send_message(f"🔊 **{membre}** n'est plus mute.")

    # ── /warn ─────────────────────────────────────────────────────────────
    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.describe(membre="Le membre à avertir", raison="Raison de l'avertissement")
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Comportement inapproprié"):
        embed = discord.Embed(
            title="⚠️ Avertissement",
            description=f"**{membre.mention}** a reçu un avertissement.",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Raison", value=raison)
        embed.add_field(name="Par", value=interaction.user.mention)
        try:
            await membre.send(f"⚠️ Tu as reçu un avertissement sur **{interaction.guild.name}**.\nRaison : {raison}")
        except discord.Forbidden:
            pass
        await interaction.response.send_message(embed=embed)

    # ── /clear ────────────────────────────────────────────────────────────
    @app_commands.command(name="clear", description="Supprimer des messages en masse")
    @app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, nombre: int = 10):
        if nombre > 100:
            await interaction.response.send_message("❌ Maximum 100 messages à la fois.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=nombre)
        await interaction.followup.send(f"🗑️ **{len(deleted)} messages** supprimés.", ephemeral=True)

    # ── Gestion des erreurs ───────────────────────────────────────────────
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Tu n'as pas les permissions nécessaires.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
