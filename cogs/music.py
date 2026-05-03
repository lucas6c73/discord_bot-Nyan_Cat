import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp

# ── Options yt-dlp ────────────────────────────────────────────────────────────
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn -bufsize 65536",
}

# ── Gestionnaire de queue par serveur ────────────────────────────────────────
class GuildPlayer:
    def __init__(self):
        self.queue: list = []
        self.current = None
        self.voice_client: discord.VoiceClient | None = None
        self.text_channel = None
        self.loop: bool = False

players: dict[int, GuildPlayer] = {}

def get_player(guild_id: int) -> GuildPlayer:
    if guild_id not in players:
        players[guild_id] = GuildPlayer()
    return players[guild_id]

# ── Cog Music ─────────────────────────────────────────────────────────────────
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def play_next(self, guild_id: int):
        p = get_player(guild_id)
        if p.loop and p.current:
            asyncio.run_coroutine_threadsafe(
                self._play_track(guild_id, p.current["data"]), self.bot.loop
            )
        elif p.queue:
            data = p.queue.pop(0)
            asyncio.run_coroutine_threadsafe(
                self._play_track(guild_id, data), self.bot.loop
            )
        else:
            p.current = None
            if p.text_channel:
                asyncio.run_coroutine_threadsafe(
                    p.text_channel.send("✅ Queue terminée ! Utilise `/play` pour ajouter une musique."),
                    self.bot.loop
                )

    async def _play_track(self, guild_id: int, data: dict):
        p = get_player(guild_id)
        if not p.voice_client or not p.voice_client.is_connected():
            return
        try:
            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(data["url"], **FFMPEG_OPTIONS),
                volume=0.5
            )
            p.current = {"source": source, "data": data}
            p.voice_client.play(source, after=lambda e: self.play_next(guild_id))

            if p.text_channel:
                dur = f"{data.get('duration', 0) // 60}:{data.get('duration', 0) % 60:02d}" if data.get("duration") else "?"
                embed = discord.Embed(title="🎵 Maintenant en lecture", color=discord.Color.green())
                embed.add_field(name="Titre", value=f"[{data.get('title','?')}]({data.get('webpage_url','')})", inline=False)
                embed.add_field(name="⏱️ Durée", value=dur, inline=True)
                if data.get("thumbnail"):
                    embed.set_thumbnail(url=data["thumbnail"])
                await p.text_channel.send(embed=embed)
        except Exception as e:
            print(f"Erreur lecture : {e}")
            if p.text_channel:
                await p.text_channel.send(f"❌ Erreur lecture : `{e}`")

    async def _get_data(self, query: str) -> dict | None:
        loop = self.bot.loop
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                q = query if query.startswith("http") else f"ytsearch:{query}"
                data = await loop.run_in_executor(None, lambda: ydl.extract_info(q, download=False))
                if "entries" in data:
                    data = data["entries"][0]
                return data
        except Exception as e:
            print(f"Erreur yt-dlp : {e}")
            return None

    # ── /play ─────────────────────────────────────────────────────────────
    @app_commands.command(name="play", description="Jouer une musique (nom ou lien YouTube)")
    @app_commands.describe(recherche="Nom de la chanson ou lien YouTube")
    async def play(self, interaction: discord.Interaction, recherche: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Tu dois être dans un salon vocal !", ephemeral=True)
            return

        await interaction.response.defer()
        p = get_player(interaction.guild_id)
        p.text_channel = interaction.channel
        voice_channel = interaction.user.voice.channel

        # Vérifier les permissions vocales
        permissions = voice_channel.permissions_for(interaction.guild.me)
        if not permissions.connect:
            await interaction.followup.send("❌ Je n'ai pas la permission de rejoindre ce salon vocal.")
            return
        if not permissions.speak:
            await interaction.followup.send("❌ Je n'ai pas la permission de parler dans ce salon vocal.")
            return

        # Connexion vocale
        try:
            if p.voice_client and p.voice_client.is_connected():
                if p.voice_client.channel.id != voice_channel.id:
                    await p.voice_client.move_to(voice_channel)
            else:
                p.voice_client = await voice_channel.connect(timeout=15.0, reconnect=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Timeout : impossible de rejoindre le salon vocal.")
            return
        except RuntimeError as e:
            if "davey library needed" in str(e).lower():
                await interaction.followup.send("❌ Erreur connexion vocale : la bibliothèque `davey` est requise pour la voix. Installe `pip install davey` et redémarre le bot.")
                return
            await interaction.followup.send(f"❌ Erreur connexion vocale : `{type(e).__name__}: {e}`")
            return
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur connexion vocale : `{type(e).__name__}: {e}`")
            return

        data = await self._get_data(recherche)
        if not data:
            await interaction.followup.send("❌ Impossible de trouver cette musique.")
            return

        dur = f"{data.get('duration', 0) // 60}:{data.get('duration', 0) % 60:02d}" if data.get("duration") else "?"

        if p.voice_client.is_playing() or p.voice_client.is_paused():
            p.queue.append(data)
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_author(name="📋 Ajouté à la queue")
            embed.add_field(name="Titre", value=f"[{data.get('title','?')}]({data.get('webpage_url','')})", inline=False)
            embed.add_field(name="⏱️ Durée", value=dur, inline=True)
            embed.add_field(name="Position", value=f"#{len(p.queue)}", inline=True)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"🔍 Chargement de **{data.get('title', '?')}**...")
            await self._play_track(interaction.guild_id, data)

    # ── /skip ─────────────────────────────────────────────────────────────
    @app_commands.command(name="skip", description="Passer à la musique suivante")
    async def skip(self, interaction: discord.Interaction):
        p = get_player(interaction.guild_id)
        if p.voice_client and (p.voice_client.is_playing() or p.voice_client.is_paused()):
            p.voice_client.stop()
            await interaction.response.send_message("⏭️ Musique passée.")
        else:
            await interaction.response.send_message("❌ Aucune musique en cours.", ephemeral=True)

    # ── /stop ─────────────────────────────────────────────────────────────
    @app_commands.command(name="stop", description="Arrêter la musique et déconnecter le bot")
    async def stop(self, interaction: discord.Interaction):
        p = get_player(interaction.guild_id)
        p.queue.clear()
        p.current = None
        p.loop = False
        if p.voice_client:
            await p.voice_client.disconnect()
            p.voice_client = None
        await interaction.response.send_message("⏹️ Musique arrêtée, bot déconnecté.")

    # ── /pause ────────────────────────────────────────────────────────────
    @app_commands.command(name="pause", description="Mettre en pause ou reprendre la musique")
    async def pause(self, interaction: discord.Interaction):
        p = get_player(interaction.guild_id)
        if not p.voice_client:
            await interaction.response.send_message("❌ Le bot n'est pas dans un vocal.", ephemeral=True)
            return
        if p.voice_client.is_playing():
            p.voice_client.pause()
            await interaction.response.send_message("⏸️ Musique mise en pause.")
        elif p.voice_client.is_paused():
            p.voice_client.resume()
            await interaction.response.send_message("▶️ Musique reprise.")
        else:
            await interaction.response.send_message("❌ Aucune musique en cours.", ephemeral=True)

    # ── /queue ────────────────────────────────────────────────────────────
    @app_commands.command(name="queue", description="Afficher la file d'attente")
    async def queue_cmd(self, interaction: discord.Interaction):
        p = get_player(interaction.guild_id)
        embed = discord.Embed(title="📋 File d'attente", color=discord.Color.blurple())
        if p.current:
            titre = p.current["data"].get("title", "?")
            embed.add_field(name="▶️ En cours", value=f"{titre} {'🔁' if p.loop else ''}", inline=False)
        else:
            embed.add_field(name="▶️ En cours", value="Rien", inline=False)
        if p.queue:
            liste = "\n".join(f"`{i+1}.` {t.get('title','?')}" for i, t in enumerate(p.queue[:10]))
            if len(p.queue) > 10:
                liste += f"\n*...et {len(p.queue)-10} autres*"
            embed.add_field(name="📝 Queue", value=liste, inline=False)
        else:
            embed.add_field(name="📝 Queue", value="Vide", inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /nowplaying ───────────────────────────────────────────────────────
    @app_commands.command(name="nowplaying", description="Voir la musique en cours de lecture")
    async def nowplaying(self, interaction: discord.Interaction):
        p = get_player(interaction.guild_id)
        if not p.current:
            await interaction.response.send_message("❌ Aucune musique en cours.", ephemeral=True)
            return
        data = p.current["data"]
        dur = f"{data.get('duration',0)//60}:{data.get('duration',0)%60:02d}" if data.get("duration") else "?"
        embed = discord.Embed(title="🎵 En cours de lecture", color=discord.Color.green())
        embed.add_field(name="Titre", value=f"[{data.get('title','?')}]({data.get('webpage_url','')})", inline=False)
        embed.add_field(name="⏱️ Durée", value=dur, inline=True)
        embed.add_field(name="🔁 Loop", value="Activé" if p.loop else "Désactivé", inline=True)
        if data.get("thumbnail"):
            embed.set_thumbnail(url=data["thumbnail"])
        await interaction.response.send_message(embed=embed)

    # ── /loop ─────────────────────────────────────────────────────────────
    @app_commands.command(name="loop", description="Activer/désactiver la répétition")
    async def loop_cmd(self, interaction: discord.Interaction):
        p = get_player(interaction.guild_id)
        p.loop = not p.loop
        state = "🔁 activée" if p.loop else "➡️ désactivée"
        await interaction.response.send_message(f"Répétition {state}.")

    # ── /volume ───────────────────────────────────────────────────────────
    @app_commands.command(name="volume", description="Régler le volume (0-100)")
    @app_commands.describe(niveau="Volume entre 0 et 100")
    async def volume(self, interaction: discord.Interaction, niveau: int):
        if not 0 <= niveau <= 100:
            await interaction.response.send_message("❌ Le volume doit être entre 0 et 100.", ephemeral=True)
            return
        p = get_player(interaction.guild_id)
        if p.voice_client and p.voice_client.source:
            p.voice_client.source.volume = niveau / 100
            await interaction.response.send_message(f"🔊 Volume réglé à **{niveau}%**.")
        else:
            await interaction.response.send_message("❌ Aucune musique en cours.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))