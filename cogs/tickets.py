import discord
from discord import app_commands
from discord.ext import commands

# Catégorie où créer les tickets (à configurer)
TICKET_CATEGORY_NAME = "TICKETS"
SUPPORT_ROLE_NAME = "Support"  # Rôle qui voit les tickets

# Stockage des tickets ouverts { user_id: channel_id }
open_tickets: dict[int, int] = {}

class TicketView(discord.ui.View):
    """Bouton 'Fermer le ticket' affiché dans le ticket."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fermeture du ticket dans 5 secondes...")
        await asyncio.sleep(5)
        # Supprimer l'entrée du dict
        to_remove = [uid for uid, cid in open_tickets.items() if cid == interaction.channel_id]
        for uid in to_remove:
            open_tickets.pop(uid, None)
        await interaction.channel.delete(reason="Ticket fermé")

class OpenTicketView(discord.ui.View):
    """Bouton 'Ouvrir un ticket' dans le panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # Vérifier si l'utilisateur a déjà un ticket ouvert
        if user.id in open_tickets:
            channel = guild.get_channel(open_tickets[user.id])
            if channel:
                await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket ouvert : {channel.mention}", ephemeral=True
                )
                return
            else:
                open_tickets.pop(user.id)

        # Trouver ou créer la catégorie
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        # Permissions du salon
        support_role = discord.utils.get(guild.roles, name=SUPPORT_ROLE_NAME)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

        # Créer le salon
        channel = await guild.create_text_channel(
            f"ticket-{user.name}",
            category=category,
            overwrites=overwrites,
            reason=f"Ticket ouvert par {user}"
        )
        open_tickets[user.id] = channel.id

        embed = discord.Embed(
            title="🎫 Ticket ouvert",
            description=(
                f"Bienvenue {user.mention} !\n\n"
                "Décris ton problème ou ta demande, l'équipe support va te répondre.\n\n"
                "Clique sur **Fermer le ticket** quand tu as eu ta réponse."
            ),
            color=discord.Color.blurple()
        )
        await channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message(
            f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True
        )

import asyncio

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Réenregistrer les vues persistantes au démarrage
        self.bot.add_view(OpenTicketView())
        self.bot.add_view(TicketView())

    # ── /ticket panel ─────────────────────────────────────────────────────
    @app_commands.command(name="ticket-panel", description="Envoyer le panel d'ouverture de tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Support & Tickets",
            description=(
                "Tu as un problème, une question ou une demande ?\n\n"
                "Clique sur le bouton ci-dessous pour ouvrir un ticket privé avec l'équipe support."
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Un seul ticket à la fois par utilisateur.")
        await interaction.channel.send(embed=embed, view=OpenTicketView())
        await interaction.response.send_message("✅ Panel de tickets envoyé !", ephemeral=True)

    # ── /ticket close ─────────────────────────────────────────────────────
    @app_commands.command(name="ticket-close", description="Fermer le ticket actuel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_close(self, interaction: discord.Interaction):
        if "ticket-" not in interaction.channel.name:
            await interaction.response.send_message("❌ Ce salon n'est pas un ticket.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Fermeture du ticket dans 5 secondes...")
        await asyncio.sleep(5)
        to_remove = [uid for uid, cid in open_tickets.items() if cid == interaction.channel_id]
        for uid in to_remove:
            open_tickets.pop(uid, None)
        await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")

    # ── /ticket add ───────────────────────────────────────────────────────
    @app_commands.command(name="ticket-add", description="Ajouter un membre au ticket actuel")
    @app_commands.describe(membre="Le membre à ajouter")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_add(self, interaction: discord.Interaction, membre: discord.Member):
        if "ticket-" not in interaction.channel.name:
            await interaction.response.send_message("❌ Ce salon n'est pas un ticket.", ephemeral=True)
            return
        await interaction.channel.set_permissions(membre, view_channel=True, send_messages=True)
        await interaction.response.send_message(f"✅ {membre.mention} a été ajouté au ticket.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
