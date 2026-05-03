import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta

# Stockage en mémoire des giveaways actifs
# { message_id: { "channel_id", "prize", "winner_count", "end_time", "host_id" } }
active_giveaways: dict[int, dict] = {}

class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /giveaway start ───────────────────────────────────────────────────
    @app_commands.command(name="giveaway", description="Lancer un giveaway")
    @app_commands.describe(
        duree="Durée en minutes",
        lot="Ce que le gagnant remporte",
        gagnants="Nombre de gagnants (1 par défaut)"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway(self, interaction: discord.Interaction, duree: int, lot: str, gagnants: int = 1):
        if duree < 1:
            await interaction.response.send_message("❌ La durée doit être d'au moins 1 minute.", ephemeral=True)
            return
        if gagnants < 1:
            await interaction.response.send_message("❌ Il faut au moins 1 gagnant.", ephemeral=True)
            return

        end_time = datetime.utcnow() + timedelta(minutes=duree)
        end_timestamp = int(end_time.timestamp())

        embed = discord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=(
                f"**{lot}**\n\n"
                f"Réagis avec 🎉 pour participer !\n\n"
                f"⏱️ Fin : <t:{end_timestamp}:R>\n"
                f"🏆 Gagnants : **{gagnants}**\n"
                f"👑 Organisé par : {interaction.user.mention}"
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Se termine le {end_time.strftime('%d/%m/%Y à %H:%M')} UTC")

        await interaction.response.send_message("✅ Giveaway lancé !", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🎉")

        active_giveaways[msg.id] = {
            "channel_id": interaction.channel_id,
            "prize": lot,
            "winner_count": gagnants,
            "end_time": end_time,
            "host_id": interaction.user.id,
            "message_id": msg.id,
        }

        # Attente asynchrone puis tirage
        await asyncio.sleep(duree * 60)
        await self._end_giveaway(msg.id)

    async def _end_giveaway(self, message_id: int):
        if message_id not in active_giveaways:
            return

        data = active_giveaways.pop(message_id)
        channel = self.bot.get_channel(data["channel_id"])
        if not channel:
            return

        try:
            msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            return

        # Récupération des participants (réaction 🎉)
        participants = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        participants.append(user)
                break

        embed = discord.Embed(title="🎉 GIVEAWAY TERMINÉ", color=discord.Color.red())
        embed.add_field(name="Lot", value=data["prize"], inline=False)

        if len(participants) < 1:
            embed.description = "😢 Personne n'a participé..."
            await msg.edit(embed=embed)
            await channel.send("😢 Aucun participant pour ce giveaway.")
            return

        nb_gagnants = min(data["winner_count"], len(participants))
        gagnants = random.sample(participants, nb_gagnants)
        mentions = " ".join(g.mention for g in gagnants)

        embed.description = f"**Gagnant(s) :** {mentions}\n👑 Organisé par <@{data['host_id']}>"
        await msg.edit(embed=embed)
        await channel.send(f"🎊 Félicitations {mentions} ! Tu as gagné **{data['prize']}** !")

    # ── /greroll ──────────────────────────────────────────────────────────
    @app_commands.command(name="greroll", description="Retirer un nouveau gagnant pour un giveaway terminé")
    @app_commands.describe(message_id="L'ID du message du giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer()
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
        except (discord.NotFound, ValueError):
            await interaction.followup.send("❌ Message introuvable.", ephemeral=True)
            return

        participants = []
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                async for user in reaction.users():
                    if not user.bot:
                        participants.append(user)
                break

        if not participants:
            await interaction.followup.send("❌ Aucun participant trouvé.")
            return

        gagnant = random.choice(participants)
        await interaction.followup.send(f"🎊 Nouveau gagnant : {gagnant.mention} ! Félicitations !")

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
