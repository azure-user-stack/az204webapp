# 🌐 Flask Incidents Réseau - Version Azure SQL Database

## 🎯 Vue d'ensemble du projet

Ce projet est la **version Azure SQL Database** de l'application Flask Incidents Réseau. Il s'agit d'une évolution de l'application originale qui utilise maintenant **Azure SQL Database** comme système de stockage cloud, offrant une solution évolutive et sécurisée pour la gestion des incidents réseau.

### 🏗️ Architecture du projet

```
flask-incidents-azure/
├── 📄 app.py                    # Application Flask principale (port 5003)
├── 📄 requirements.txt          # Dépendances Python avec versions compatibles
├── 📄 README.md                 # Documentation complète de configuration
├── 📄 init_azure_database.sql   # Script d'initialisation Azure SQL Database
├── 📄 diagnostic_azure.py       # Diagnostic complet de l'environnement Azure
├── 📄 test_azure_connection.py  # Test rapide de connexion Azure SQL
└── 📁 templates/
    ├── 📄 incidents.html        # Page principale avec branding Azure
    ├── 📄 detail.html          # Détail d'un incident avec design cloud
    └── 📄 ajouter.html         # Formulaire d'ajout avec interface Azure
```

## 🚀 Fonctionnalités

### ✨ Fonctionnalités principales
- **📋 Gestion d'incidents réseau** : Affichage, création, consultation détaillée
- **🔒 Stockage cloud sécurisé** : Données stockées dans Azure SQL Database
- **🎨 Interface utilisateur moderne** : Design adapté avec thème Azure/Cloud
- **📊 API REST intégrée** : Accès programmatique aux données via `/api/incidents`
- **🔧 Outils de diagnostic** : Tests de connexion et diagnostic complet

### 🆕 Nouveautés version Azure
- **☁️ Branding Azure** : Interface utilisateur avec couleurs et icônes Microsoft Azure
- **🔐 Connexion chiffrée** : Communication sécurisée avec Azure SQL Database
- **📊 Monitoring intégré** : Statut de connexion et métriques de performance
- **🧪 Outils de diagnostic** : Scripts automatisés pour tester la configuration Azure
- **🌐 Variables d'environnement** : Configuration flexible pour différents environnements

## 🔧 Configuration technique

### 📋 Prérequis
- **Python 3.13** (testé et compatible)
- **Azure SQL Database** configurée et accessible
- **ODBC Driver 18 for SQL Server** installé
- **Variables d'environnement** Azure configurées

### 📦 Dépendances principales
```
Flask==2.3.3                    # Framework web Python
SQLAlchemy==1.4.53              # ORM compatible Python 3.13
Flask-SQLAlchemy==2.5.1         # Intégration Flask/SQLAlchemy
pyodbc==4.0.39                  # Driver Azure SQL Database
azure-identity==1.15.0          # Authentification Azure (optionnel)
```

### 🔑 Variables d'environnement requises
```
AZURE_SQL_SERVER=votre-serveur.database.windows.net
AZURE_SQL_DATABASE=votre-base-de-donnees
AZURE_SQL_USERNAME=votre-utilisateur
AZURE_SQL_PASSWORD=votre-mot-de-passe
```

## 🎯 Utilisation

### 🚀 Démarrage rapide
```powershell
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Configurer les variables d'environnement Azure
# (voir README.md pour les détails)

# 3. Initialiser la base de données Azure
# Exécuter init_azure_database.sql dans Azure

# 4. Tester la connexion
python test_azure_connection.py

# 5. Lancer l'application
python app.py
```

### 🔍 Tests et diagnostic
```powershell
# Test rapide de connexion
python test_azure_connection.py

# Diagnostic complet de l'environnement
python diagnostic_azure.py
```

### 🌐 Accès à l'application
- **🏠 Interface principale** : http://localhost:5003
- **📊 Statut Azure SQL** : http://localhost:5003/azure-status
- **🧪 Test connexion** : http://localhost:5003/test-azure
- **📡 API REST** : http://localhost:5003/api/incidents

## 📊 Fonctionnalités de l'interface

### 🏠 Page d'accueil (`/`)
- **📋 Liste des incidents** : Affichage en grille avec design Azure
- **⚡ Indicateur de sévérité** : Code couleur pour les niveaux d'urgence
- **☁️ Statut Azure SQL** : Indicateur de connexion en temps réel
- **➕ Ajout rapide** : Bouton d'accès direct au formulaire

### 📄 Détail d'incident (`/incident/<id>`)
- **📋 Informations complètes** : Titre, sévérité, description, dates
- **☁️ Métadonnées Azure** : Information sur la source de données cloud
- **🔗 Navigation fluide** : Liens vers la liste et l'ajout d'incidents

### ➕ Formulaire d'ajout (`/ajouter`)
- **📝 Saisie guidée** : Formulaire avec validation et aide contextuelle
- **⚡ Sélection sévérité** : Menu déroulant avec aperçu visuel
- **💾 Sauvegarde Azure** : Enregistrement direct dans Azure SQL Database
- **✅ Validation temps réel** : Contrôles JavaScript et serveur

### 🔧 Pages de diagnostic
- **📊 Statut Azure** (`/azure-status`) : Métriques détaillées de connexion
- **🧪 Test connexion** (`/test-azure`) : Vérification rapide de la base de données

## 🔒 Sécurité et bonnes pratiques

### 🛡️ Sécurité des données
- **🔐 Connexion chiffrée** : `Encrypt=yes` pour toutes les communications
- **🚫 Certificats vérifiés** : `TrustServerCertificate=no` pour la validation SSL
- **⏱️ Timeout configuré** : Protection contre les connexions lentes
- **🔑 Gestion des secrets** : Variables d'environnement pour les identifiants

### 📈 Performance et monitoring
- **🔍 Index optimisés** : Index sur date_incident et sévérité pour des requêtes rapides
- **📊 Métriques intégrées** : Monitoring des temps de connexion et de requête
- **🔄 Gestion des erreurs** : Récupération gracieuse en cas de problème réseau

## 🎉 Évolution depuis les versions précédentes

### 📈 Évolution du projet
1. **🥇 Version 1** : `flask-incidents-reseau` - Stockage en mémoire (port 5000)
2. **🥈 Version 2** : `flask-incidents-sqlserver` - SQL Server local (port 5001)
3. **🥉 Version 3** : `flask-incidents-azure` - Azure SQL Database (port 5003) ← **Actuelle**

### ✨ Améliorations version Azure
- **☁️ Infrastructure cloud** : Évolutivité et disponibilité Azure
- **🎨 Design modernisé** : Interface avec thème Microsoft Azure
- **🔧 Outils avancés** : Scripts de diagnostic et de test automatisés
- **📚 Documentation complète** : Guide détaillé de configuration Azure
- **🔒 Sécurité renforcée** : Chiffrement et authentification cloud

## 📞 Support et ressources

### 📚 Documentation
- **📖 README.md** : Guide complet de configuration et déploiement
- **🔧 Scripts de diagnostic** : Outils automatisés pour résoudre les problèmes
- **📊 Commentaires code** : Documentation technique intégrée

### 🆘 Résolution de problèmes
1. **🧪 Test rapide** : `python test_azure_connection.py`
2. **🔍 Diagnostic complet** : `python diagnostic_azure.py`
3. **📚 Consultation** : Vérification du README.md pour les étapes détaillées
4. **🔧 Azure Portal** : Contrôle des ressources et configuration firewall

---

## 🏁 Résumé

Cette application Flask Incidents Réseau version Azure représente une solution cloud moderne et évolutive pour la gestion des incidents réseau. Elle combine la simplicité de Flask avec la puissance et la sécurité d'Azure SQL Database, tout en offrant une interface utilisateur moderne et des outils de diagnostic avancés.

**🚀 Prêt pour le développement et la production sur Azure !**