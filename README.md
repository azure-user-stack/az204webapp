# 🌐 Configuration Azure SQL Database - Flask Incidents Réseau

## 📋 Vue d'ensemble

Cette version de l'application Flask Incidents Réseau utilise **Azure SQL Database** comme base de données cloud. Ce guide vous accompagne dans la configuration complète de l'environnement Azure et du déploiement de l'application.

## 🏗️ Architecture de la solution

```
Application Flask (Port 5003)
           ↓
    Variables d'environnement
           ↓
   Chaîne de connexion Azure SQL
           ↓
    Azure SQL Database (Cloud)
```

## 🔧 Prérequis

### 1. Environnement de développement
- **Python 3.13** (testé et compatible)
- **pip** (gestionnaire de paquets Python)
- **Git** (pour le contrôle de version)

### 2. Ressources Azure
- **Abonnement Azure actif**
- **Azure SQL Database** créée et configurée
- **Règles de pare-feu Azure** configurées
- **Utilisateur de base de données** avec permissions appropriées

## 🚀 Installation étape par étape

### Étape 1 : Cloner le projet
```powershell
# Cloner le repository
git clone [URL_DU_REPOSITORY]
cd flask-incidents-azure

# Ou copier depuis le projet existant
cp -r ../flask-incidents-sqlserver/* .
```

### Étape 2 : Créer l'environnement virtuel Python
```powershell
# Créer l'environnement virtuel
python -m venv venv-azure

# Activer l'environnement (Windows)
.\venv-azure\Scripts\Activate.ps1

# Ou sur Linux/Mac
source venv-azure/bin/activate
```

### Étape 3 : Installer les dépendances
```powershell
# Installer les packages requis
pip install -r requirements.txt

# Installation optimisée pour pyodbc (version précompilée)
pip install --only-binary=all pyodbc
```

### Étape 4 : Configuration Azure SQL Database

#### 4.1 Création de la base de données Azure
1. **Connectez-vous au portail Azure** : https://portal.azure.com
2. **Créer un serveur SQL Azure** :
   - Nom du serveur : `votre-serveur-sql`
   - Authentification : SQL Server Authentication
   - Admin utilisateur : `votre-admin`
   - Mot de passe : `VotreMotDePasseComplexe!`
   - Région : Europe Ouest (ou votre région préférée)

3. **Créer la base de données** :
   - Nom : `incidents-reseau-db`
   - Niveau de service : Basic ou Standard (selon besoins)
   - Taille : 2 GB (suffisant pour débuter)

#### 4.2 Configuration du pare-feu
```powershell
# Ajouter votre adresse IP publique aux règles de pare-feu Azure
# Via Azure CLI (optionnel)
az sql server firewall-rule create \
  --resource-group votre-groupe-ressources \
  --server votre-serveur-sql \
  --name "DevMachine" \
  --start-ip-address VOTRE_IP \
  --end-ip-address VOTRE_IP
```

### Étape 5 : Configuration des variables d'environnement

#### 5.1 Méthode 1 : Variables système Windows
```powershell
# Définir les variables d'environnement (PowerShell Admin)
[Environment]::SetEnvironmentVariable("AZURE_SQL_SERVER", "votre-serveur.database.windows.net", "User")
[Environment]::SetEnvironmentVariable("AZURE_SQL_DATABASE", "incidents-reseau-db", "User")
[Environment]::SetEnvironmentVariable("AZURE_SQL_USERNAME", "votre-admin", "User")
[Environment]::SetEnvironmentVariable("AZURE_SQL_PASSWORD", "VotreMotDePasseComplexe!", "User")

# Redémarrer PowerShell pour prendre en compte les variables
```

#### 5.2 Méthode 2 : Fichier .env (recommandé pour dev)
```powershell
# Créer un fichier .env dans le répertoire du projet
@"
AZURE_SQL_SERVER=votre-serveur.database.windows.net
AZURE_SQL_DATABASE=incidents-reseau-db
AZURE_SQL_USERNAME=votre-admin
AZURE_SQL_PASSWORD=VotreMotDePasseComplexe!
"@ | Out-File -FilePath .env -Encoding utf8
```

### Étape 6 : Initialisation de la base de données
```powershell
# Se connecter à Azure SQL Database avec SQL Server Management Studio (SSMS)
# Ou utiliser Azure Data Studio
# Exécuter le script : init_azure_database.sql

# Alternative avec sqlcmd (si installé)
sqlcmd -S votre-serveur.database.windows.net -d incidents-reseau-db -U votre-admin -P VotreMotDePasseComplexe! -i init_azure_database.sql
```

### Étape 7 : Test de l'application
```powershell
# Lancer l'application Flask
python app.py

# L'application sera disponible sur http://localhost:5003
```

## 🔍 Tests et diagnostics

### Test de connexion Azure SQL
```powershell
# Tester la connexion depuis l'application
# Aller sur : http://localhost:5003/test-azure
# Ou : http://localhost:5003/azure-status
```

### Script de diagnostic autonome
```python
# Créer un fichier test_azure_connection.py
import os
import pyodbc
from sqlalchemy import create_engine

def test_azure_connection():
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    print(f"🔧 Test connexion Azure SQL Database")
    print(f"📍 Serveur: {server}")
    print(f"💾 Base: {database}")
    print(f"👤 Utilisateur: {username}")
    
    try:
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            result = conn.execute("SELECT @@VERSION").fetchone()
            print(f"✅ Connexion réussie !")
            print(f"📊 Version SQL: {result[0][:50]}...")
            return True
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    test_azure_connection()
```

## 🔒 Sécurité et bonnes pratiques

### 1. Gestion des secrets
```powershell
# Ne jamais commiter les mots de passe dans Git
echo ".env" >> .gitignore
echo "*.env" >> .gitignore

# Utiliser Azure Key Vault pour la production
```

### 2. Connexion sécurisée
- ✅ **Chiffrement activé** : `Encrypt=yes`
- ✅ **Certificats validés** : `TrustServerCertificate=no`
- ✅ **Timeout configuré** : `Connection+Timeout=30`
- ✅ **Driver moderne** : `ODBC Driver 18 for SQL Server`

### 3. Permissions minimales
```sql
-- Créer un utilisateur dédié pour l'application
CREATE USER [flask_app_user] WITH PASSWORD = 'MotDePasseRobuste123!';

-- Donner uniquement les permissions nécessaires
ALTER ROLE db_datareader ADD MEMBER [flask_app_user];
ALTER ROLE db_datawriter ADD MEMBER [flask_app_user];

-- Permissions sur les tables spécifiques
GRANT SELECT, INSERT, UPDATE ON incidents TO [flask_app_user];
```

## 📊 Monitoring et performance

### 1. Surveillance Azure SQL
- **Azure Monitor** : Métriques de performance en temps réel
- **Query Performance Insight** : Analyse des requêtes lentes
- **Alertes automatiques** : Sur l'utilisation CPU/Mémoire

### 2. Optimisation des requêtes
```sql
-- Index pour optimiser les recherches
CREATE NONCLUSTERED INDEX IX_incidents_date_severite
ON incidents (date_incident DESC, severite)
INCLUDE (titre, description);

-- Statistiques de performance
SELECT 
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    dm_os.counter_name,
    dm_os.cntr_value
FROM sys.dm_os_performance_counters dm_os
INNER JOIN sys.indexes i ON i.object_id = OBJECT_ID('incidents')
WHERE dm_os.object_name LIKE '%Buffer Manager%';
```

## 🚀 Déploiement en production

### 1. Azure App Service
```yaml
# azure-pipelines.yml pour CI/CD
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.13'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '$(pythonVersion)'
  displayName: 'Use Python $(pythonVersion)'

- script: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
  displayName: 'Install dependencies'

- task: AzureWebApp@1
  inputs:
    azureSubscription: 'votre-subscription'
    appType: 'webAppLinux'
    appName: 'flask-incidents-azure'
    package: '.'
```

### 2. Configuration App Service
```powershell
# Variables d'environnement App Service
az webapp config appsettings set \
  --resource-group votre-groupe \
  --name flask-incidents-azure \
  --settings \
    AZURE_SQL_SERVER="votre-serveur.database.windows.net" \
    AZURE_SQL_DATABASE="incidents-reseau-db" \
    AZURE_SQL_USERNAME="votre-admin" \
    AZURE_SQL_PASSWORD="VotreMotDePasseComplexe!"
```

## 🆘 Résolution de problèmes

### Problème 1 : "Login failed for user"
```
❌ Erreur : Login failed for user 'votre-admin'
✅ Solution :
1. Vérifier les identifiants Azure SQL
2. Contrôler les règles de pare-feu
3. Tester la connexion depuis SSMS
```

### Problème 2 : "Driver not found"
```
❌ Erreur : [Microsoft][ODBC Driver Manager] Data source name not found
✅ Solution :
1. Installer ODBC Driver 18 for SQL Server
2. Vérifier la chaîne de connexion
3. Redémarrer l'application
```

### Problème 3 : "Connection timeout"
```
❌ Erreur : Connection timeout expired
✅ Solution :
1. Augmenter Connection_Timeout=60
2. Vérifier la latence réseau
3. Optimiser les requêtes SQL
```

## 📞 Support et ressources

### Documentation officielle
- **Azure SQL Database** : https://docs.microsoft.com/azure/sql-database/
- **Flask-SQLAlchemy** : https://flask-sqlalchemy.palletsprojects.com/
- **pyodbc** : https://github.com/mkleehammer/pyodbc

### Outils utiles
- **Azure Data Studio** : Client SQL moderne et gratuit
- **SSMS** : SQL Server Management Studio
- **Azure CLI** : Gestion des ressources Azure
- **Postman** : Test des API REST de l'application

### Contact
- **Développeur** : [Votre nom]
- **Version** : 1.0.0 (Azure SQL Edition)
- **Dernière MAJ** : [Date actuelle]

---

## 🎉 Félicitations !

Votre application Flask Incidents Réseau est maintenant configurée pour utiliser Azure SQL Database ! 

🔗 **Accès à l'application** : http://localhost:5003
📊 **Diagnostic Azure** : http://localhost:5003/azure-status
🧪 **Test connexion** : http://localhost:5003/test-azure

L'application est prête pour le développement et peut être déployée sur Azure App Service pour la production.