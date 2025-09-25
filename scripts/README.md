# Scripts de Déploiement Azure Web App

Ce dossier contient les scripts et templates nécessaires pour déployer une application web Azure avec App Service Plan Linux.

## 📁 Contenu du Dossier

- **`arm-template.json`** : Template ARM (Azure Resource Manager) pour déployer les ressources
- **`deploy-webapp.ps1`** : Script PowerShell pour Windows
- **`deploy-webapp.sh`** : Script Bash pour Linux/macOS
- **`README.md`** : Ce fichier de documentation

## 🏗️ Architecture Déployée

Le template déploie les ressources suivantes :

1. **App Service Plan** (Linux)
   - SKU configurable (Free, Basic, Standard, Premium)
   - Support des runtimes Linux (Python, Node.js, .NET, etc.)
   - Workers configurables

2. **Web App**
   - Application web Linux
   - HTTPS uniquement
   - Credentials de base désactivés pour la sécurité
   - Configuration optimisée pour la production

3. **Politiques de Sécurité**
   - Désactivation des credentials FTP/SCM
   - Configuration sécurisée par défaut

## 🚀 Utilisation

### Prérequis

- Azure CLI installé et configuré
- Connexion à Azure (`az login`)
- Permissions suffisantes dans l'abonnement Azure

### Windows (PowerShell)

```powershell
# Déploiement basique
.\deploy-webapp.ps1 -ResourceGroupName "mon-rg" -WebAppName "mon-app"

# Déploiement avec options personnalisées
.\deploy-webapp.ps1 `
    -ResourceGroupName "mon-rg" `
    -WebAppName "mon-app" `
    -Location "West Europe" `
    -Sku "Standard" `
    -SkuCode "S1" `
    -LinuxFxVersion "NODE|18-lts"
```

### Linux/macOS (Bash)

```bash
# Rendre le script exécutable
chmod +x deploy-webapp.sh

# Déploiement basique
./deploy-webapp.sh -g "mon-rg" -n "mon-app"

# Déploiement avec options personnalisées
./deploy-webapp.sh \
    -g "mon-rg" \
    -n "mon-app" \
    -l "West Europe" \
    -s "Standard" \
    -c "S1" \
    -r "NODE|18-lts"
```

## 🔧 Paramètres de Configuration

### Paramètres Obligatoires

| Paramètre | Description | PowerShell | Bash |
|-----------|-------------|------------|------|
| Groupe de ressources | Nom du groupe de ressources | `-ResourceGroupName` | `-g`, `--resource-group` |
| Nom de l'app | Nom de l'application web | `-WebAppName` | `-n`, `--name` |

### Paramètres Optionnels

| Paramètre | Description | Défaut | PowerShell | Bash |
|-----------|-------------|--------|------------|------|
| Localisation | Région Azure | France Central | `-Location` | `-l`, `--location` |
| Plan d'hébergement | Nom du App Service Plan | {nom-app}-plan | `-AppServicePlanName` | `-p`, `--plan` |
| SKU | Niveau de tarification | Basic | `-Sku` | `-s`, `--sku` |
| Code SKU | Code du niveau | B1 | `-SkuCode` | `-c`, `--sku-code` |
| Runtime | Version du runtime Linux | PYTHON\|3.11 | `-LinuxFxVersion` | `-r`, `--runtime` |

## 🐍 Runtimes Supportés

### Python
- `PYTHON|3.8`
- `PYTHON|3.9`
- `PYTHON|3.10`
- `PYTHON|3.11`

### Node.js
- `NODE|16-lts`
- `NODE|18-lts`
- `NODE|20-lts`

### .NET
- `DOTNETCORE|6.0`
- `DOTNETCORE|7.0`
- `DOTNETCORE|8.0`

### PHP
- `PHP|8.0`
- `PHP|8.1`
- `PHP|8.2`

## 💰 Niveaux de Tarification (SKU)

| Niveau | Code | Description | Use Case |
|--------|------|-------------|----------|
| Free | F1 | Gratuit avec limitations | Tests, développement |
| Shared | D1 | Partagé avec quotas | Petits projets |
| Basic | B1, B2, B3 | Ressources dédiées | Applications de production |
| Standard | S1, S2, S3 | Fonctionnalités avancées | Applications métier |
| Premium | P1, P2, P3 | Haute performance | Applications critiques |

## 🔐 Sécurité

Le template implémente les bonnes pratiques de sécurité :

- **HTTPS uniquement** : Redirection automatique HTTP → HTTPS
- **Credentials désactivés** : FTP/SCM credentials désactivés
- **Logging activé** : Logs HTTP, tracing, et erreurs détaillées
- **App Service Storage** : Désactivé pour les conteneurs
- **Run from Package** : Mode de déploiement sécurisé

## 📊 Post-Déploiement

### Configuration des Variables d'Environnement

```bash
# Ajouter des variables d'environnement
az webapp config appsettings set \
    --name "mon-app" \
    --resource-group "mon-rg" \
    --settings \
        DATABASE_URL="votre-url-db" \
        SECRET_KEY="votre-cle-secrete"
```

### Déploiement du Code

#### Via Azure CLI
```bash
# Déploiement depuis un dossier local
az webapp up --name "mon-app" --resource-group "mon-rg"

# Déploiement depuis un ZIP
az webapp deployment source config-zip \
    --name "mon-app" \
    --resource-group "mon-rg" \
    --src "app.zip"
```

#### Via Git
```bash
# Configuration du déploiement Git
az webapp deployment source config \
    --name "mon-app" \
    --resource-group "mon-rg" \
    --repo-url "https://github.com/user/repo.git" \
    --branch "main"
```

## 🔍 Monitoring et Diagnostics

### Application Insights
```bash
# Créer une instance Application Insights
az monitor app-insights component create \
    --app "mon-app-insights" \
    --location "France Central" \
    --resource-group "mon-rg"

# Lier à la Web App
az webapp config appsettings set \
    --name "mon-app" \
    --resource-group "mon-rg" \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY="votre-clé"
```

### Logs
```bash
# Activer les logs
az webapp log config \
    --name "mon-app" \
    --resource-group "mon-rg" \
    --application-logging filesystem \
    --web-server-logging filesystem

# Consulter les logs
az webapp log tail --name "mon-app" --resource-group "mon-rg"
```

## 🚨 Dépannage

### Erreurs Communes

1. **Nom d'application déjà utilisé**
   - Les noms de Web App sont globalement uniques
   - Utilisez un nom plus spécifique

2. **Quota dépassé**
   - Vérifiez les quotas de votre abonnement
   - Changez de région si nécessaire

3. **Permissions insuffisantes**
   - Vérifiez les permissions RBAC
   - Role minimum requis : Contributeur

### Commandes de Diagnostic

```bash
# Vérifier l'état de l'application
az webapp show --name "mon-app" --resource-group "mon-rg"

# Lister les déploiements
az deployment group list --resource-group "mon-rg"

# Consulter les métriques
az monitor metrics list \
    --resource "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Web/sites/{app}"
```

## 🔄 Nettoyage

Pour supprimer toutes les ressources créées :

```bash
# Supprimer le groupe de ressources complet
az group delete --name "mon-rg" --yes --no-wait

# Ou supprimer uniquement la Web App
az webapp delete --name "mon-app" --resource-group "mon-rg"
```

## 📚 Ressources Supplémentaires

- [Documentation Azure App Service](https://docs.microsoft.com/en-us/azure/app-service/)
- [Templates ARM](https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/)
- [Azure CLI Reference](https://docs.microsoft.com/en-us/cli/azure/)
- [Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)

---

**Note** : Assurez-vous de personnaliser les paramètres selon vos besoins spécifiques et de suivre les bonnes pratiques de sécurité pour la production.