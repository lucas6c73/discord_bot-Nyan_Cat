import discord
from discord import app_commands
from discord.ext import commands
import json
import os

ROLES_FILE = "role_panels.json"

def load_panels() -> dict:
    if os.path.exists(ROLES_FILE):
        with open(ROLES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_panels(data: dict):
    with open(ROLES_FILE, "w") as f:
        json.dump(data, f, indent=2)

class RoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str = None):
        super().__init__(
            label=label,
            emoji=emoji or None,
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_{role_id}"
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ Rôle introuvable.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ Rôle **{role.name}** retiré.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rôle **{role.name}** attribué !", ephemeral=True)

class RolePanelView(discord.ui.View):
    def __init__(self, roles: list[dict]):
        super().__init__(timeout=None)
        for r in roles:
            self.add_item(RoleButton(
                role_id=r["role_id"],
                label=r["label"],
                emoji=r.get("emoji")
            ))

class AutoRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.panels = load_panels()
        # Réenregistrer les vues persistantes au démarrage
        for panel_data in self.panels.values():
            self.bot.add_view(RolePanelView(panel_data["roles"]))

    # ── /roles-panel ──────────────────────────────────────────────────────
    @app_commands.command(name="roles-panel", description="Créer un panel de rôles automatiques avec boutons")
    @app_commands.describe(
        titre="Titre du panel",
        description="Description du panel"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def roles_panel(self, interaction: discord.Interaction, titre: str, description: str = "Clique sur un bouton pour obtenir un rôle !"):
        # Démarrer une session modale pour ajouter des rôles
        await interaction.response.send_message(
            "✅ Panel initialisé ! Utilise `/roles-add` pour ajouter des rôles au panel, "
            "puis `/roles-send` pour l'envoyer.",
            ephemeral=True
        )
        guild_key = str(interaction.guild_id)
        self.panels[guild_key] = {
            "titre": titre,
            "description": description,
            "channel_id": interaction.channel_id,
            "roles": []
        }
        save_panels(self.panels)

    # ── /roles-add ────────────────────────────────────────────────────────
    @app_commands.command(name="roles-add", description="Ajouter un rôle au panel en cours de création")
    @app_commands.describe(
        role="Le rôle à ajouter",
        label="Texte du bouton",
        emoji="Emoji du bouton (optionnel)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def roles_add(self, interaction: discord.Interaction, role: discord.Role, label: str, emoji: str = None):
        guild_key = str(interaction.guild_id)
        if guild_key not in self.panels:
            await interaction.response.send_message("❌ Aucun panel en cours. Utilise `/roles-panel` d'abord.", ephemeral=True)
            return

        if len(self.panels[guild_key]["roles"]) >= 25:
            await interaction.response.send_message("❌ Maximum 25 rôles par panel.", ephemeral=True)
            return

        self.panels[guild_key]["roles"].append({
            "role_id": role.id,
            "label": label,
            "emoji": emoji
        })
        save_panels(self.panels)

        count = len(self.panels[guild_key]["roles"])
        await interaction.response.send_message(
            f"✅ Rôle **{role.name}** ajouté ! ({count} rôle(s) dans le panel)\n"
            f"Utilise `/roles-send` pour envoyer le panel quand tu as terminé.",
            ephemeral=True
        )

    # ── /roles-send ───────────────────────────────────────────────────────
    @app_commands.command(name="roles-send", description="Envoyer le panel de rôles dans ce salon")
    @app_commands.checks.has_permissions(administrator=True)
    async def roles_send(self, interaction: discord.Interaction):
        guild_key = str(interaction.guild_id)
        if guild_key not in self.panels or not self.panels[guild_key]["roles"]:
            await interaction.response.send_message("❌ Aucun panel prêt. Utilise `/roles-panel` et `/roles-add` d'abord.", ephemeral=True)
            return

        data = self.panels[guild_key]
        embed = discord.Embed(
            title=data["titre"],
            description=data["description"],
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Clique sur un bouton pour obtenir ou retirer un rôle.")

        view = RolePanelView(data["roles"])
        self.bot.add_view(view)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Panel envoyé !", ephemeral=True)

    # ── /roles-list ───────────────────────────────────────────────────────
    @app_commands.command(name="roles-list", description="Voir les rôles du panel en cours")
    @app_commands.checks.has_permissions(administrator=True)
    async def roles_list(self, interaction: discord.Interaction):
        guild_key = str(interaction.guild_id)
        if guild_key not in self.panels:
            await interaction.response.send_message("❌ Aucun panel en cours.", ephemeral=True)
            return

        data = self.panels[guild_key]
        if not data["roles"]:
            await interaction.response.send_message("📋 Le panel est vide.", ephemeral=True)
            return

        lines = []
        for i, r in enumerate(data["roles"]):
            role = interaction.guild.get_role(r["role_id"])
            name = role.mention if role else f"Rôle supprimé ({r['role_id']})"
            lines.append(f"`{i+1}.` {r.get('emoji','')} **{r['label']}** → {name}")

        embed = discord.Embed(
            title=f"📋 Panel : {data['titre']}",
            description="\n".join(lines),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRoles(bot))
