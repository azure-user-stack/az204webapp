# Scripts de Déploiement Base de Données SQL Server Azure

Ce dossier contient les scripts pour déployer une base de données SQL Server sur Azure en utilisant Azure CLI.

## Prérequis

1. **Azure CLI installé** : [Installation d'Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. **Compte Azure actif** avec les permissions appropriées
3. **PowerShell** (pour Windows) ou **Bash** (pour Linux/macOS)

## Scripts Disponibles

### 1. PowerShell Script (Windows)
**Fichier** : `deploy-sqlserver-azure.ps1`

#### Utilisation
```powershell
# Exemple d'utilisation
.\deploy-sqlserver-azure.ps1 `
    -ResourceGroupName "rg-incidents-prod" `
    -ServerName "srv-incidents-db" `
    -DatabaseName "db-incidents" `
    -Location "France central" `
    -AdminUsername "sqladmin" `
    -AdminPassword (ConvertTo-SecureString "MotDePasse123!" -AsPlainText -Force)
```

#### Paramètres
- `ResourceGroupName` : Nom du groupe de ressources Azure
- `ServerName` : Nom du serveur SQL (doit être unique globalement)
- `DatabaseName` : Nom de la base de données
- `Location` : Région Azure (défaut: "East US")
- `AdminUsername` : Nom d'utilisateur administrateur
- `AdminPassword` : Mot de passe administrateur (SecureString)
- `ServiceTier` : Niveau de service (défaut: "Basic")

### 2. Bash Script (Linux/macOS)
**Fichier** : `deploy-sqlserver-azure.sh`

#### Utilisation
```bash
# Rendre le script exécutable
chmod +x deploy-sqlserver-azure.sh

# Exemple d'utilisation
./deploy-sqlserver-azure.sh \
    -g "rg-incidents-prod" \
    -s "srv-incidents-db" \
    -d "db-incidents" \
    -l "francecentral" \
    -u "sqladmin" \
    -p "MotDePasse123!"
```

#### Options
- `-g, --resource-group` : Nom du groupe de ressources
- `-s, --server-name` : Nom du serveur SQL
- `-d, --database-name` : Nom de la base de données
- `-l, --location` : Localisation Azure (défaut: eastus)
- `-u, --admin-user` : Nom d'utilisateur administrateur
- `-p, --admin-password` : Mot de passe administrateur
- `-t, --service-tier` : Niveau de service (défaut: Basic)
- `-h, --help` : Afficher l'aide

## Fonctionnalités

Les scripts effectuent automatiquement :

1. ✅ **Vérification des prérequis** (Azure CLI installé et connexion)
2. ✅ **Création du groupe de ressources** (si nécessaire)
3. ✅ **Création du serveur SQL Server**
4. ✅ **Configuration des règles de pare-feu** :
   - Autorisation des services Azure
   - Autorisation de l'IP locale
5. ✅ **Création de la base de données**
6. ✅ **Génération de la chaîne de connexion**

## Sécurité

- Les mots de passe sont gérés de manière sécurisée
- Les règles de pare-feu sont configurées automatiquement
- L'IP locale est automatiquement détectée et autorisée

## Niveaux de Service Disponibles

- **Basic** : Pour le développement et les tests
- **Standard** : Pour la production légère
- **Premium** : Pour les charges de travail critiques

## Après le Déploiement

1. **Mise à jour du fichier .env** :
```env
DB_SERVER=votre-serveur.database.windows.net
DB_DATABASE=nom-de-votre-db
DB_USERNAME=sqladmin
DB_PASSWORD=MotDePasse123!
DB_DRIVER={ODBC Driver 17 for SQL Server}
```

2. **Exécution du script d'initialisation** :
```bash
python init_azure_database.py
```

## Troubleshooting

### Erreurs Communes

1. **"Server name already exists"**
   - Le nom du serveur doit être unique globalement
   - Essayez un nom différent

2. **"Insufficient permissions"**
   - Vérifiez que votre compte a les rôles appropriés dans Azure

3. **"Azure CLI not found"**
   - Installez Azure CLI et redémarrez votre terminal

4. **"Login required"**
   - Exécutez `az login` pour vous connecter à Azure

## Support

Pour plus d'informations sur Azure SQL Database :
- [Documentation officielle](https://docs.microsoft.com/en-us/azure/azure-sql/database/)
- [Pricing Azure SQL Database](https://azure.microsoft.com/en-us/pricing/details/azure-sql-database/single/)

## Exemples d'Utilisation

### Déploiement pour Développement
```powershell
# Windows
.\deploy-sqlserver-azure.ps1 `
    -ResourceGroupName "rg-dev-incidents" `
    -ServerName "srv-dev-incidents-$(Get-Random)" `
    -DatabaseName "db-incidents-dev" `
    -AdminUsername "devadmin" `
    -AdminPassword (ConvertTo-SecureString "DevPass123!" -AsPlainText -Force) `
    -ServiceTier "Basic"
```

```bash
# Linux/macOS
./deploy-sqlserver-azure.sh \
    -g "rg-dev-incidents" \
    -s "srv-dev-incidents-$RANDOM" \
    -d "db-incidents-dev" \
    -u "devadmin" \
    -p "DevPass123!" \
    -t "Basic"
```

### Déploiement pour Production
```powershell
# Windows
.\deploy-sqlserver-azure.ps1 `
    -ResourceGroupName "rg-prod-incidents" `
    -ServerName "srv-prod-incidents" `
    -DatabaseName "db-incidents-prod" `
    -Location "West Europe" `
    -AdminUsername "prodadmin" `
    -AdminPassword (ConvertTo-SecureString "StrongProdPass123!" -AsPlainText -Force) `
    -ServiceTier "Standard"
```