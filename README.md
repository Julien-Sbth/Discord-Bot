# 🤖 Bot Discord de Diffusion d'Offres d'Emploi

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Discord.py](https://img.shields.io/badge/Discord.py-2.0%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Un bot Discord qui collecte, analyse et diffuse automatiquement les meilleures offres d'emploi via des fichier json.

## 🔑 Configuration Obligatoire

### 1. Créer un Bot Discord
1. Allez sur le [Portail Développeur Discord](https://discord.com/developers/applications)
2. Créez une nouvelle application
3. Allez dans l'onglet "Bot" et cliquez "Add Bot"
4. Copiez le **TOKEN** (c'est votre clé API)

### 2. Obtenir la clé API Apify
1. Créez un compte sur [Apify](https://console.apify.com/sign-up)
2. Allez dans [Paramètres du compte](https://console.apify.com/account#/integrations)
3. Dans la section "API Tokens", cliquez sur "Show" pour révéler votre token
4. Copiez ce token pour l'utiliser dans le fichier .env

### 3. Comment générer un fichier JSON sur Apify ?

1. **Accéder au Store Apify** :
   - Rendez-vous sur le [Store Apify](https://console.apify.com/store).
2. **Rechercher le scraper Indeed** :
   - Utilisez la barre de recherche pour trouver le scraper "Indeed".
3. **Configurer les paramètres de recherche** :
   - **Positions/Mots-clés** : Entrez un titre de poste, par exemple "alternance cybersécurité".
   - **Pays** : Sélectionnez le pays cible pour votre recherche.
   - **Ville** : Indiquez la ville où vous souhaitez effectuer la recherche.
   - **Nombre maximum d'items** : Définissez le nombre maximum de résultats que vous souhaitez obtenir.
4. **Exécuter le scraper** :
   - Lancez le scraper avec les paramètres configurés pour récupérer les données.
5. **Récupérer les détails des entreprises** :
   - Apify permet de scraper les détails des entreprises, tels que les descriptions de poste, les avis, etc.
6. **Télécharger le fichier JSON** :
   - Une fois le scraping terminé, vous pouvez télécharger les résultats au format JSON pour une utilisation ultérieure.
   - Placez le fichier dans le dossier `json/offers`.

### 3. Configurer le Fichier .env
Créez un fichier `.env` à la racine du projet avec :

```ini
# Configuration Discord (OBLIGATOIRE)
DISCORD_TOKEN="votre_token_discord_ici"
CHANNEL_ID="123456789012345678"  # ID du canal où poster

# Configuration APIFY
APIFY_API_KEY="votre_cle_api_ici"
```
## 🛠️ Fonctionnalité à implémenter
### ✨ Auto-Apply (Assistance à la Candidature)

**⚠️ Remarque** : Cette fonctionnalité ne postule pas automatiquement en votre nom. Elle vise plutôt à simplifier et accélérer le processus en générant des informations personnalisées pour chaque offre.


