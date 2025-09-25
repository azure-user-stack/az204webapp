#!/bin/bash

# Script de déploiement SQL Server sur Azure (Bash)
# Auteur: Azure DevOps Team
# Date: 2025-09-24

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonction d'aide
show_help() {
    echo "Usage: $0 -g RESOURCE_GROUP -s SERVER_NAME -d DATABASE_NAME -l LOCATION -u ADMIN_USER -p ADMIN_PASSWORD"
    echo ""
    echo "Options:"
    echo "  -g, --resource-group    Nom du groupe de ressources"
    echo "  -s, --server-name       Nom du serveur SQL"
    echo "  -d, --database-name     Nom de la base de données"
    echo "  -l, --location          Localisation Azure (défaut: eastus)"
    echo "  -u, --admin-user        Nom d'utilisateur administrateur"
    echo "  -p, --admin-password    Mot de passe administrateur"
    echo "  -t, --service-tier      Niveau de service (défaut: Basic)"
    echo "  -h, --help              Afficher cette aide"
    echo ""
    echo "Exemple:"
    echo "  $0 -g myResourceGroup -s myserver -d mydatabase -u adminuser -p 'MyPassword123!'"
}

# Variables par défaut
LOCATION="eastus"
SERVICE_TIER="Basic"

# Traitement des paramètres
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -s|--server-name)
            SERVER_NAME="$2"
            shift 2
            ;;
        -d|--database-name)
            DATABASE_NAME="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -u|--admin-user)
            ADMIN_USER="$2"
            shift 2
            ;;
        -p|--admin-password)
            ADMIN_PASSWORD="$2"
            shift 2
            ;;
        -t|--service-tier)
            SERVICE_TIER="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Vérification des paramètres requis
if [[ -z "$RESOURCE_GROUP" || -z "$SERVER_NAME" || -z "$DATABASE_NAME" || -z "$ADMIN_USER" || -z "$ADMIN_PASSWORD" ]]; then
    echo -e "${RED}Erreur: Paramètres requis manquants${NC}"
    show_help
    exit 1
fi

echo -e "${GREEN}=== Déploiement SQL Server sur Azure ===${NC}"
echo "Resource Group: $RESOURCE_GROUP"
echo "Server Name: $SERVER_NAME"
echo "Database Name: $DATABASE_NAME"
echo "Location: $LOCATION"
echo ""

# Vérifier si Azure CLI est installé
echo -e "${YELLOW}Vérification d'Azure CLI...${NC}"
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI n'est pas installé. Veuillez l'installer d'abord.${NC}"
    exit 1
fi

az --version
if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de la vérification d'Azure CLI${NC}"
    exit 1
fi

# Se connecter à Azure (si nécessaire)
echo -e "${YELLOW}Vérification de la connexion Azure...${NC}"
ACCOUNT=$(az account show --query "user.name" -o tsv 2>/dev/null)
if [ -z "$ACCOUNT" ]; then
    echo -e "${YELLOW}Connexion à Azure requise...${NC}"
    az login
    if [ $? -ne 0 ]; then
        echo -e "${RED}Échec de la connexion à Azure${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Connecté en tant que: $ACCOUNT${NC}"
fi

# Créer le groupe de ressources s'il n'existe pas
echo -e "${YELLOW}Création/Vérification du groupe de ressources...${NC}"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
if [ $? -ne 0 ]; then
    echo -e "${RED}Échec de la création du groupe de ressources${NC}"
    exit 1
fi

# Créer le serveur SQL Server
echo -e "${YELLOW}Création du serveur SQL Server...${NC}"
az sql server create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$SERVER_NAME" \
    --location "$LOCATION" \
    --admin-user "$ADMIN_USER" \
    --admin-password "$ADMIN_PASSWORD"

if [ $? -ne 0 ]; then
    echo -e "${RED}Échec de la création du serveur SQL${NC}"
    exit 1
fi

# Configurer les règles de pare-feu
echo -e "${YELLOW}Configuration des règles de pare-feu...${NC}"

# Autoriser les services Azure
az sql server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --server "$SERVER_NAME" \
    --name "AllowAzureServices" \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# Autoriser l'IP locale (optionnel)
LOCAL_IP=$(curl -s https://ipinfo.io/ip)
echo -e "${YELLOW}Configuration de l'accès pour l'IP locale: $LOCAL_IP${NC}"
az sql server firewall-rule create \
    --resource-group "$RESOURCE_GROUP" \
    --server "$SERVER_NAME" \
    --name "AllowLocalIP" \
    --start-ip-address "$LOCAL_IP" \
    --end-ip-address "$LOCAL_IP"

# Créer la base de données
echo -e "${YELLOW}Création de la base de données...${NC}"
az sql db create \
    --resource-group "$RESOURCE_GROUP" \
    --server "$SERVER_NAME" \
    --name "$DATABASE_NAME" \
    --service-objective "$SERVICE_TIER"

if [ $? -ne 0 ]; then
    echo -e "${RED}Échec de la création de la base de données${NC}"
    exit 1
fi

# Obtenir la chaîne de connexion
echo -e "${YELLOW}Récupération des informations de connexion...${NC}"
CONNECTION_STRING="Server=tcp:$SERVER_NAME.database.windows.net,1433;Initial Catalog=$DATABASE_NAME;Persist Security Info=False;User ID=$ADMIN_USER;Password=***;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"

echo ""
echo -e "${GREEN}=== DÉPLOIEMENT RÉUSSI ===${NC}"
echo -e "${GREEN}Serveur SQL: $SERVER_NAME.database.windows.net${NC}"
echo -e "${GREEN}Base de données: $DATABASE_NAME${NC}"
echo -e "${YELLOW}Chaîne de connexion (sans mot de passe):${NC}"
echo -e "${CYAN}$CONNECTION_STRING${NC}"
echo ""
echo -e "${YELLOW}N'oubliez pas de configurer votre fichier .env avec ces informations!${NC}"
echo ""
echo -e "${GREEN}Script terminé avec succès!${NC}"