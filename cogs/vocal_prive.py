import discord
from discord import app_commands
from discord.ext import commands

# Nom du salon "hub" à rejoindre pour créer son vocal privé
HUB_CHANNEL_NAME = "➕ Créer un vocal"

# { user_id: channel_id } - salons privés en cours
private_channels: dict[int, int] = {}

class VocalPriveView(discord.ui.View):
    """Panneau de contrôle du vocal privé."""
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Seul le propriétaire du vocal peut utiliser ces boutons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🔒 Verrouiller", style=discord.ButtonStyle.danger, custom_id="vc_lock")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            await interaction.response.send_message("❌ Tu n'es pas dans un vocal.", ephemeral=True)
            return
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Vocal verrouillé.", ephemeral=True)

    @discord.ui.button(label="🔓 Déverrouiller", style=discord.ButtonStyle.success, custom_id="vc_unlock")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            await interaction.response.send_message("❌ Tu n'es pas dans un vocal.", ephemeral=True)
            return
        await channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Vocal déverrouillé.", ephemeral=True)

    @discord.ui.button(label="👁️ Masquer", style=discord.ButtonStyle.secondary, custom_id="vc_hide")
    async def hide(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            await interaction.response.send_message("❌ Tu n'es pas dans un vocal.", ephemeral=True)
            return
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message("👁️ Vocal masqué.", ephemeral=True)

    @discord.ui.button(label="👁️ Afficher", style=discord.ButtonStyle.secondary, custom_id="vc_show")
    async def show(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.user.voice.channel if interaction.user.voice else None
        if not channel:
            await interaction.response.send_message("❌ Tu n'es pas dans un vocal.", ephemeral=True)
            return
        await channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message("👁️ Vocal visible.", ephemeral=True)

class VocalPrive(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild

        # Rejoindre le hub → créer un vocal privé
        if after.channel and after.channel.name == HUB_CHANNEL_NAME:
            category = after.channel.category

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
                member: discord.PermissionOverwrite(
                    connect=True, manage_channels=True, mute_members=True,
                    deafen_members=True, move_members=True, view_channel=True
                ),
                guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True, view_channel=True),
            }

            channel = await guild.create_voice_channel(
                f"🔊 Vocal de {member.display_name}",
                category=category,
                overwrites=overwrites,
                reason="Vocal privé créé automatiquement"
            )
            private_channels[member.id] = channel.id
            await member.move_to(channel)

            # Envoyer le panneau de contrôle en MP
            try:
                embed = discord.Embed(
                    title="🎙️ Ton vocal privé est prêt !",
                    description=f"**{channel.name}** a été créé.\nUtilise les boutons ci-dessous pour le gérer.",
                    color=discord.Color.blurple()
                )
                await member.send(embed=embed, view=VocalPriveView(member.id))
            except discord.Forbidden:
                pass

        # Quitter un vocal privé vide → supprimer
        if before.channel and before.channel.id in private_channels.values():
            if len(before.channel.members) == 0:
                owner_id = next((uid for uid, cid in private_channels.items() if cid == before.channel.id), None)
                if owner_id:
                    private_channels.pop(owner_id, None)
                try:
                    await before.channel.delete(reason="Vocal privé vide")
                except discord.NotFound:
                    pass

    # ── /vocal-setup ──────────────────────────────────────────────────────
    @app_commands.command(name="vocal-setup", description="Créer le salon hub pour les vocaux privés")
    @app_commands.checks.has_permissions(administrator=True)
    async def vocal_setup(self, interaction: discord.Interaction):
        guild = interaction.guild
        existing = discord.utils.get(guild.voice_channels, name=HUB_CHANNEL_NAME)
        if existing:
            await interaction.response.send_message(f"❌ Le salon **{HUB_CHANNEL_NAME}** existe déjà : {existing.mention}", ephemeral=True)
            return

        category = discord.utils.get(guild.categories, name="VOCAL")
        channel = await guild.create_voice_channel(HUB_CHANNEL_NAME, category=category)
        await interaction.response.send_message(
            f"✅ Salon hub créé : **{channel.name}**\nLes membres qui le rejoignent auront leur propre vocal privé !"
        )

    # ── /vocal-kick ───────────────────────────────────────────────────────
    @app_commands.command(name="vocal-kick", description="Expulser un membre de ton vocal privé")
    @app_commands.describe(membre="Le membre à expulser")
    async def vocal_kick(self, interaction: discord.Interaction, membre: discord.Member):
        if interaction.user.id not in private_channels:
            await interaction.response.send_message("❌ Tu n'as pas de vocal privé actif.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(private_channels[interaction.user.id])
        if not channel or membre not in channel.members:
            await interaction.response.send_message("❌ Ce membre n'est pas dans ton vocal.", ephemeral=True)
            return
        await membre.move_to(None)
        await channel.set_permissions(membre, connect=False)
        await interaction.response.send_message(f"✅ {membre.mention} a été expulsé de ton vocal.", ephemeral=True)

    # ── /vocal-invite ─────────────────────────────────────────────────────
    @app_commands.command(name="vocal-invite", description="Inviter un membre dans ton vocal privé verrouillé")
    @app_commands.describe(membre="Le membre à inviter")
    async def vocal_invite(self, interaction: discord.Interaction, membre: discord.Member):
        if interaction.user.id not in private_channels:
            await interaction.response.send_message("❌ Tu n'as pas de vocal privé actif.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(private_channels[interaction.user.id])
        if not channel:
            await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
            return
        await channel.set_permissions(membre, connect=True, view_channel=True)
        await interaction.response.send_message(f"✅ {membre.mention} peut maintenant rejoindre ton vocal !")
        try:
            await membre.send(f"🎙️ Tu as été invité dans le vocal privé de **{interaction.user.display_name}** sur **{interaction.guild.name}** !")
        except discord.Forbidden:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(VocalPrive(bot))
