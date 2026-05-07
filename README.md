# discord_Bot

Nyan_cat_project

C'est mon premier projet donc soyer indulgeant svp. Lors de ce projet l'IA  a été utiliser pour les tache suivante :

- Ecriture du read et du processus d'installation.
- Création des phrases aléatoire pour les blague, clash etc...
- Optimisation du code : suppression des boucle, résolution des problème mineur et majeur et supression des variable répétée.


# 🤖 Bot Discord Multifonctions

Un bot Discord complet avec 9 modules : modération, musique, niveaux, tickets, giveaways et plus encore. Toutes les commandes utilisent le système de **Slash Commands** (`/`) de Discord.

---

## 📦 Modules disponibles

| Module | Description |
|--------|-------------|
| 🛡️ Modération | Ban, kick, mute, warn, clear |
| ℹ️ Information | Infos membre, serveur, avatar, ping |
| 🎮 Fun | Blagues, dé, 8ball, RPS, clash |
| 🎵 Musique | Lecteur YouTube avec file d'attente |
| 🎉 Giveaway | Tirages au sort automatiques |
| 🎫 Tickets | Support avec salons privés |
| ⭐ Niveaux | Système d'XP et de progression |
| 🔊 Vocal Privé | Salons vocaux personnels automatiques |
| 🎭 AutoRôles | Panels de rôles interactifs |

---

## ⚙️ Installation

### Prérequis

- Python 3.10+
- Un token de bot Discord

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/lucas6c73/discord_bot-Nyan_Cat/
cd ton-bot

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer le token
cp .env.example .env
# Édite .env et ajoute ton token Discord

# 4. Lancer le bot
python main.py
```

### Fichier `.env`

```env
DISCORD_TOKEN=ton_token_ici
```

### Dépendances (`requirements.txt`)

```
discord.py
python-dotenv
yt-dlp
PyNaCl
```

---

## 📁 Structure du projet

```
├── main.py
├── .env
├── requirements.txt
├── xp_data.json          # Données XP (généré automatiquement)
├── role_panels.json      # Panels de rôles (généré automatiquement)
└── cogs/
    ├── moderation.py
    ├── info.py
    ├── fun.py
    ├── music.py
    ├── giveaway.py
    ├── tickets.py
    ├── levels.py
    ├── vocal_prive.py
    └── autoroles.py
```

---

## 📋 Commandes

### 🛡️ Modération

| Commande | Description | Permission |
|----------|-------------|------------|
| `/ban <membre> [raison]` | Bannir un membre | `ban_members` |
| `/kick <membre> [raison]` | Expulser un membre | `kick_members` |
| `/mute <membre> [durée] [raison]` | Mettre en timeout (en minutes) | `moderate_members` |
| `/unmute <membre>` | Retirer le timeout | `moderate_members` |
| `/warn <membre> [raison]` | Avertir un membre | `kick_members` |
| `/clear [nombre]` | Supprimer des messages (max 100) | `manage_messages` |

### ℹ️ Information

| Commande | Description |
|----------|-------------|
| `/userinfo [membre]` | Fiche complète d'un membre |
| `/serverinfo` | Statistiques du serveur |
| `/avatar [membre]` | Avatar en haute résolution |
| `/ping` | Latence du bot |
| `/stats` | Statistiques globales du bot |

### 🎮 Fun

| Commande | Description |
|----------|-------------|
| `/8ball <question>` | Boule magique |
| `/pile` | Pile ou Face |
| `/de [faces]` | Lancer un dé |
| `/blague` | Blague aléatoire |
| `/chiffre` | Nombre aléatoire entre 1 et 100 |
| `/rps <choix>` | Pierre, Feuille, Ciseaux |
| `/clash <membre>` | Clash humoristique |

### 🎵 Musique

> Tu dois être dans un salon vocal pour utiliser ces commandes.

| Commande | Description |
|----------|-------------|
| `/play <recherche>` | Jouer une musique (nom ou lien YouTube) |
| `/skip` | Passer à la suivante |
| `/stop` | Arrêter et déconnecter le bot |
| `/pause` | Pause / Reprendre |
| `/queue` | Afficher la file d'attente |
| `/nowplaying` | Musique en cours |
| `/loop` | Activer / désactiver la répétition |
| `/volume <0-100>` | Régler le volume |

### 🎉 Giveaway

| Commande | Description | Permission |
|----------|-------------|------------|
| `/giveaway <durée> <lot> [gagnants]` | Lancer un giveaway | `manage_guild` |
| `/greroll <message_id>` | Tirer un nouveau gagnant | `manage_guild` |

### 🎫 Tickets

| Commande | Description | Permission |
|----------|-------------|------------|
| `/ticket-panel` | Poster le panel d'ouverture | `administrator` |
| `/ticket-close` | Fermer le ticket actuel | `manage_channels` |
| `/ticket-add <membre>` | Ajouter un membre au ticket | `manage_channels` |

> **Note :** Crée un rôle nommé exactement `Support` pour que l'équipe accède aux tickets.

### ⭐ Niveaux & XP

| Commande | Description | Permission |
|----------|-------------|------------|
| `/rank [membre]` | Fiche de niveau et barre de progression | — |
| `/leaderboard` | Top 10 du serveur | — |
| `/xp-add <membre> <quantité>` | Ajouter de l'XP manuellement | `administrator` |

> Les membres gagnent entre **5 et 15 XP** par message, avec un cooldown de **60 secondes**.

### 🔊 Vocal Privé

| Commande | Description | Permission |
|----------|-------------|------------|
| `/vocal-setup` | Créer le salon hub (à faire une fois) | `administrator` |
| `/vocal-kick <membre>` | Expulser un membre de son vocal | — |
| `/vocal-invite <membre>` | Inviter quelqu'un dans son vocal | — |

> Rejoindre le salon **➕ Créer un vocal** crée automatiquement un salon vocal privé. Il est supprimé dès qu'il est vide.

### 🎭 AutoRôles

| Commande | Description | Permission |
|----------|-------------|------------|
| `/roles-panel <titre> [description]` | Initialiser un panel | `administrator` |
| `/roles-add <role> <label> [emoji]` | Ajouter un rôle au panel | `administrator` |
| `/roles-send` | Publier le panel | `administrator` |
| `/roles-list` | Voir les rôles configurés | `administrator` |

> **Workflow :** `/roles-panel` → `/roles-add` (répéter) → `/roles-send`

---

## 🔒 Permissions Discord requises

Pour fonctionner correctement, le bot a besoin des permissions suivantes :

- Lire et envoyer des messages
- Gérer les messages
- Gérer les salons
- Gérer les rôles
- Expulser et bannir des membres
- Modérer les membres (timeout)
- Se connecter et parler en vocal
- Ajouter des réactions

---

## 📝 Licence

Ce projet est un projet open source donc n'hésiter a le modifier comme vous le souhaiter.
