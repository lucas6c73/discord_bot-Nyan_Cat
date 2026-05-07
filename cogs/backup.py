import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime

BACKUP_DIR = "backups"

def ensure_backup_dir():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def backup_filename(guild_id: int, label: str = None) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    name = f"{label}_{timestamp}" if label else timestamp
    return os.path.join(BACKUP_DIR, f"backup_{guild_id}_{name}.json")

def list_backups(guild_id: int) -> list[dict]:
    ensure_backup_dir()
    files = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.startswith(f"backup_{guild_id}_") and f.endswith(".json"):
            path = os.path.join(BACKUP_DIR, f)
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            files.append({
                "filename": f,
                "path": path,
                "date": datetime.utcfromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S"),
                "size_kb": round(size / 1024, 1),
            })
    return files

class Backup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /save ─────────────────────────────────────────────────────────────
    @app_commands.command(name="save", description="Sauvegarder la configuration complète du serveur")
    @app_commands.describe(label="Nom optionnel pour identifier la sauvegarde")
    @app_commands.checks.has_permissions(administrator=True)
    async def save(self, interaction: discord.Interaction, label: str = None):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        ensure_backup_dir()

        backup = {
            "meta": {
                "guild_id": guild.id,
                "guild_name": guild.name,
                "saved_at": datetime.utcnow().isoformat(),
                "saved_by": str(interaction.user),
                "label": label or "",
            },
            "guild": {
                "name": guild.name,
                "description": guild.description or "",
                "afk_timeout": guild.afk_timeout,
                "verification_level": str(guild.verification_level),
                "default_notifications": str(guild.default_notifications),
                "explicit_content_filter": str(guild.explicit_content_filter),
                "system_channel_id": guild.system_channel.id if guild.system_channel else None,
                "rules_channel_id": guild.rules_channel.id if guild.rules_channel else None,
            },
            "roles": [],
            "categories": [],
            "text_channels": [],
            "voice_channels": [],
        }

        # ── Rôles ─────────────────────────────────────────────────────────
        for role in guild.roles:
            if role.is_default():
                continue
            backup["roles"].append({
                "id": role.id,
                "name": role.name,
                "color": role.color.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "position": role.position,
                "permissions": role.permissions.value,
            })

        # ── Catégories ────────────────────────────────────────────────────
        for cat in guild.categories:
            overwrites = {}
            for target, overwrite in cat.overwrites.items():
                key = f"role_{target.id}" if isinstance(target, discord.Role) else f"member_{target.id}"
                allow, deny = overwrite.pair()
                overwrites[key] = {"allow": allow.value, "deny": deny.value}

            backup["categories"].append({
                "id": cat.id,
                "name": cat.name,
                "position": cat.position,
                "overwrites": overwrites,
            })

        # ── Salons texte ──────────────────────────────────────────────────
        for ch in guild.text_channels:
            overwrites = {}
            for target, overwrite in ch.overwrites.items():
                key = f"role_{target.id}" if isinstance(target, discord.Role) else f"member_{target.id}"
                allow, deny = overwrite.pair()
                overwrites[key] = {"allow": allow.value, "deny": deny.value}

            backup["text_channels"].append({
                "id": ch.id,
                "name": ch.name,
                "topic": ch.topic or "",
                "position": ch.position,
                "nsfw": ch.is_nsfw(),
                "slowmode_delay": ch.slowmode_delay,
                "category_id": ch.category_id,
                "overwrites": overwrites,
            })

        # ── Salons vocaux ─────────────────────────────────────────────────
        for ch in guild.voice_channels:
            overwrites = {}
            for target, overwrite in ch.overwrites.items():
                key = f"role_{target.id}" if isinstance(target, discord.Role) else f"member_{target.id}"
                allow, deny = overwrite.pair()
                overwrites[key] = {"allow": allow.value, "deny": deny.value}

            backup["voice_channels"].append({
                "id": ch.id,
                "name": ch.name,
                "position": ch.position,
                "user_limit": ch.user_limit,
                "bitrate": ch.bitrate,
                "category_id": ch.category_id,
                "overwrites": overwrites,
            })

        # ── Sauvegarde JSON ───────────────────────────────────────────────
        path = backup_filename(guild.id, label)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)

        size_kb = round(os.path.getsize(path) / 1024, 1)
        filename = os.path.basename(path)

        embed = discord.Embed(
            title="✅ Sauvegarde créée",
            color=discord.Color.green()
        )
        embed.add_field(name="📁 Fichier", value=f"`{filename}`", inline=False)
        embed.add_field(name="🏷️ Label", value=label or "*(aucun)*", inline=True)
        embed.add_field(name="📦 Taille", value=f"{size_kb} Ko", inline=True)
        embed.add_field(name="🎭 Rôles", value=len(backup["roles"]), inline=True)
        embed.add_field(name="📁 Catégories", value=len(backup["categories"]), inline=True)
        embed.add_field(name="💬 Salons texte", value=len(backup["text_channels"]), inline=True)
        embed.add_field(name="🔊 Salons vocaux", value=len(backup["voice_channels"]), inline=True)
        embed.set_footer(text=f"Sauvegardé par {interaction.user}")

        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /backup-list ──────────────────────────────────────────────────────
    @app_commands.command(name="backup-list", description="Lister toutes les sauvegardes disponibles")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_list(self, interaction: discord.Interaction):
        backups = list_backups(interaction.guild_id)
        if not backups:
            await interaction.response.send_message("❌ Aucune sauvegarde trouvée pour ce serveur.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📋 Sauvegardes disponibles",
            color=discord.Color.blurple()
        )
        lines = []
        for i, b in enumerate(backups[:15]):
            lines.append(f"`{i+1}.` **{b['filename']}**\n    📅 {b['date']} — {b['size_kb']} Ko")

        embed.description = "\n".join(lines)
        embed.set_footer(text="Utilise /restore <nom_fichier> pour restaurer une sauvegarde.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /restore ──────────────────────────────────────────────────────────
    @app_commands.command(name="restore", description="Restaurer une sauvegarde du serveur")
    @app_commands.describe(fichier="Nom du fichier de sauvegarde (visible dans /backup-list)")
    @app_commands.checks.has_permissions(administrator=True)
    async def restore(self, interaction: discord.Interaction, fichier: str):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        path = os.path.join(BACKUP_DIR, fichier)

        if not os.path.exists(path):
            await interaction.followup.send(f"❌ Fichier introuvable : `{fichier}`\nUtilise `/backup-list` pour voir les sauvegardes disponibles.", ephemeral=True)
            return

        with open(path, "r", encoding="utf-8") as f:
            backup = json.load(f)

        if backup["meta"]["guild_id"] != guild.id:
            await interaction.followup.send("❌ Cette sauvegarde n'appartient pas à ce serveur.", ephemeral=True)
            return

        errors = []
        restored = {"roles": 0, "categories": 0, "text_channels": 0, "voice_channels": 0}

        # ── Restauration des rôles ─────────────────────────────────────────
        # Correspondance ancien_id -> nouveau rôle
        role_map: dict[int, discord.Role] = {}

        for role_data in sorted(backup["roles"], key=lambda r: r["position"]):
            existing = discord.utils.get(guild.roles, name=role_data["name"])
            try:
                if existing:
                    await existing.edit(
                        color=discord.Color(role_data["color"]),
                        hoist=role_data["hoist"],
                        mentionable=role_data["mentionable"],
                        permissions=discord.Permissions(role_data["permissions"]),
                        reason="Restauration sauvegarde"
                    )
                    role_map[role_data["id"]] = existing
                else:
                    new_role = await guild.create_role(
                        name=role_data["name"],
                        color=discord.Color(role_data["color"]),
                        hoist=role_data["hoist"],
                        mentionable=role_data["mentionable"],
                        permissions=discord.Permissions(role_data["permissions"]),
                        reason="Restauration sauvegarde"
                    )
                    role_map[role_data["id"]] = new_role
                restored["roles"] += 1
            except Exception as e:
                errors.append(f"Rôle `{role_data['name']}` : {e}")

        def build_overwrites(raw: dict) -> dict:
            result = {}
            for key, val in raw.items():
                if key.startswith("role_"):
                    rid = int(key[5:])
                    target = role_map.get(rid) or guild.get_role(rid)
                elif key.startswith("member_"):
                    mid = int(key[7:])
                    target = guild.get_member(mid)
                else:
                    continue
                if target is None:
                    continue
                overwrite = discord.PermissionOverwrite.from_pair(
                    discord.Permissions(val["allow"]),
                    discord.Permissions(val["deny"])
                )
                result[target] = overwrite
            return result

        # ── Restauration des catégories ───────────────────────────────────
        cat_map: dict[int, discord.CategoryChannel] = {}

        for cat_data in sorted(backup["categories"], key=lambda c: c["position"]):
            existing = discord.utils.get(guild.categories, name=cat_data["name"])
            overwrites = build_overwrites(cat_data.get("overwrites", {}))
            try:
                if existing:
                    await existing.edit(position=cat_data["position"], reason="Restauration sauvegarde")
                    cat_map[cat_data["id"]] = existing
                else:
                    new_cat = await guild.create_category(
                        name=cat_data["name"],
                        overwrites=overwrites,
                        reason="Restauration sauvegarde"
                    )
                    cat_map[cat_data["id"]] = new_cat
                restored["categories"] += 1
            except Exception as e:
                errors.append(f"Catégorie `{cat_data['name']}` : {e}")

        # ── Restauration des salons texte ─────────────────────────────────
        for ch_data in sorted(backup["text_channels"], key=lambda c: c["position"]):
            existing = discord.utils.get(guild.text_channels, name=ch_data["name"])
            category = cat_map.get(ch_data.get("category_id")) or guild.get_channel(ch_data.get("category_id"))
            overwrites = build_overwrites(ch_data.get("overwrites", {}))
            try:
                if existing:
                    await existing.edit(
                        topic=ch_data["topic"] or None,
                        nsfw=ch_data["nsfw"],
                        slowmode_delay=ch_data["slowmode_delay"],
                        category=category,
                        reason="Restauration sauvegarde"
                    )
                else:
                    await guild.create_text_channel(
                        name=ch_data["name"],
                        topic=ch_data["topic"] or None,
                        nsfw=ch_data["nsfw"],
                        slowmode_delay=ch_data["slowmode_delay"],
                        category=category,
                        overwrites=overwrites,
                        reason="Restauration sauvegarde"
                    )
                restored["text_channels"] += 1
            except Exception as e:
                errors.append(f"Salon texte `{ch_data['name']}` : {e}")

        # ── Restauration des salons vocaux ────────────────────────────────
        for ch_data in sorted(backup["voice_channels"], key=lambda c: c["position"]):
            existing = discord.utils.get(guild.voice_channels, name=ch_data["name"])
            category = cat_map.get(ch_data.get("category_id")) or guild.get_channel(ch_data.get("category_id"))
            overwrites = build_overwrites(ch_data.get("overwrites", {}))
            try:
                if existing:
                    await existing.edit(
                        user_limit=ch_data["user_limit"],
                        bitrate=min(ch_data["bitrate"], guild.bitrate_limit),
                        category=category,
                        reason="Restauration sauvegarde"
                    )
                else:
                    await guild.create_voice_channel(
                        name=ch_data["name"],
                        user_limit=ch_data["user_limit"],
                        bitrate=min(ch_data["bitrate"], guild.bitrate_limit),
                        category=category,
                        overwrites=overwrites,
                        reason="Restauration sauvegarde"
                    )
                restored["voice_channels"] += 1
            except Exception as e:
                errors.append(f"Salon vocal `{ch_data['name']}` : {e}")

        # ── Résumé ────────────────────────────────────────────────────────
        embed = discord.Embed(
            title="✅ Restauration terminée",
            color=discord.Color.green() if not errors else discord.Color.orange()
        )
        embed.add_field(name="📅 Sauvegarde du", value=backup["meta"]["saved_at"][:19].replace("T", " "), inline=False)
        embed.add_field(name="🎭 Rôles", value=restored["roles"], inline=True)
        embed.add_field(name="📁 Catégories", value=restored["categories"], inline=True)
        embed.add_field(name="💬 Salons texte", value=restored["text_channels"], inline=True)
        embed.add_field(name="🔊 Salons vocaux", value=restored["voice_channels"], inline=True)

        if errors:
            embed.add_field(
                name=f"⚠️ {len(errors)} erreur(s)",
                value="\n".join(errors[:5]) + ("\n*...et d'autres*" if len(errors) > 5 else ""),
                inline=False
            )

        embed.set_footer(text=f"Restauré par {interaction.user}")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ── /backup-delete ────────────────────────────────────────────────────
    @app_commands.command(name="backup-delete", description="Supprimer une sauvegarde")
    @app_commands.describe(fichier="Nom du fichier à supprimer (visible dans /backup-list)")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_delete(self, interaction: discord.Interaction, fichier: str):
        path = os.path.join(BACKUP_DIR, fichier)
        if not os.path.exists(path):
            await interaction.response.send_message(f"❌ Fichier introuvable : `{fichier}`", ephemeral=True)
            return
        os.remove(path)
        await interaction.response.send_message(f"🗑️ Sauvegarde `{fichier}` supprimée.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Backup(bot))
