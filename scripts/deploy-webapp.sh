#!/bin/bash

# ===============================================
# Script de déploiement Azure Web App (Linux/macOS)
# Déploie une Web App Linux avec App Service Plan
# ===============================================

set -euo pipefail

# ===============================================
# Configuration par défaut
# ===============================================
LOCATION="France Central"
SKU="Basic"
SKU_CODE="B1"
LINUX_FX_VERSION="PYTHON|3.11"
TEMPLATE_FILE="./arm-template.json"

# ===============================================
# Fonctions utilitaires
# ===============================================
print_info() {
    echo -e "\033[36mℹ️  $1\033[0m"
}

print_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

print_warning() {
    echo -e "\033[33m⚠️  $1\033[0m"
}

print_usage() {
    echo "Usage: $0 -g <resource-group> -n <web-app-name> [options]"
    echo ""
    echo "Options obligatoires:"
    echo "  -g, --resource-group    Nom du groupe de ressources"
    echo "  -n, --name             Nom de l'application web"
    echo ""
    echo "Options facultatives:"
    echo "  -l, --location         Localisation Azure (défaut: France Central)"
    echo "  -p, --plan             Nom du plan d'hébergement (défaut: <nom-app>-plan)"
    echo "  -s, --sku              Niveau SKU (défaut: Basic)"
    echo "  -c, --sku-code         Code SKU (défaut: B1)"
    echo "  -r, --runtime          Runtime Linux (défaut: PYTHON|3.11)"
    echo "  -t, --template         Fichier template ARM (défaut: ./arm-template.json)"
    echo "  -h, --help             Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 -g myResourceGroup -n myWebApp"
    echo "  $0 -g myRG -n myApp -l \"West Europe\" -s Standard -c S1"
}

# ===============================================
# Analyse des arguments
# ===============================================
while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -n|--name)
            WEB_APP_NAME="$2"
            shift 2
            ;;
        -l|--location)
            LOCATION="$2"
            shift 2
            ;;
        -p|--plan)
            APP_SERVICE_PLAN_NAME="$2"
            shift 2
            ;;
        -s|--sku)
            SKU="$2"
            shift 2
            ;;
        -c|--sku-code)
            SKU_CODE="$2"
            shift 2
            ;;
        -r|--runtime)
            LINUX_FX_VERSION="$2"
            shift 2
            ;;
        -t|--template)
            TEMPLATE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            print_error "Option inconnue: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Vérification des paramètres obligatoires
if [[ -z "${RESOURCE_GROUP:-}" ]] || [[ -z "${WEB_APP_NAME:-}" ]]; then
    print_error "Les paramètres -g (resource-group) et -n (name) sont obligatoires"
    print_usage
    exit 1
fi

# Configuration du nom du plan d'hébergement par défaut
APP_SERVICE_PLAN_NAME="${APP_SERVICE_PLAN_NAME:-${WEB_APP_NAME}-plan}"

# ===============================================
# Vérification des prérequis
# ===============================================
print_info "Vérification des prérequis..."

# Vérifier si Azure CLI est installé
if ! command -v az &> /dev/null; then
    print_error "Azure CLI n'est pas installé. Installez-le depuis: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Vérifier la version d'Azure CLI
AZ_VERSION=$(az version --query '"azure-cli"' -o tsv)
print_success "Azure CLI version $AZ_VERSION détecté"

# Vérifier si l'utilisateur est connecté
if ! az account show &> /dev/null; then
    print_error "Vous n'êtes pas connecté à Azure. Utilisez 'az login'"
    exit 1
fi

ACCOUNT_NAME=$(az account show --query name -o tsv)
print_success "Connecté à Azure: $ACCOUNT_NAME"

# Vérifier si le template existe
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    print_error "Le fichier template '$TEMPLATE_FILE' n'existe pas"
    exit 1
fi

# ===============================================
# Variables de déploiement
# ===============================================
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
DEPLOYMENT_NAME="webapp-deployment-$TIMESTAMP"

print_info "Configuration du déploiement:"
echo "  • Subscription ID: $SUBSCRIPTION_ID"
echo "  • Resource Group: $RESOURCE_GROUP"
echo "  • Web App Name: $WEB_APP_NAME"
echo "  • Location: $LOCATION"
echo "  • App Service Plan: $APP_SERVICE_PLAN_NAME"
echo "  • SKU: $SKU ($SKU_CODE)"
echo "  • Runtime: $LINUX_FX_VERSION"

# ===============================================
# Création du groupe de ressources
# ===============================================
print_info "Vérification/Création du groupe de ressources..."

if az group exists --name "$RESOURCE_GROUP" | grep -q "false"; then
    print_info "Création du groupe de ressources $RESOURCE_GROUP..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    print_success "Groupe de ressources créé avec succès"
else
    print_success "Groupe de ressources $RESOURCE_GROUP existe déjà"
fi

# ===============================================
# Déploiement du template ARM
# ===============================================
print_info "Démarrage du déploiement ARM..."

# Création du fichier de paramètres temporaire
PARAM_FILE=$(mktemp)
cat > "$PARAM_FILE" << EOF
{
    "subscriptionId": {"value": "$SUBSCRIPTION_ID"},
    "resourceGroupName": {"value": "$RESOURCE_GROUP"},
    "name": {"value": "$WEB_APP_NAME"},
    "location": {"value": "$LOCATION"},
    "hostingPlanName": {"value": "$APP_SERVICE_PLAN_NAME"},
    "serverFarmResourceGroup": {"value": "$RESOURCE_GROUP"},
    "alwaysOn": {"value": true},
    "ftpsState": {"value": "Disabled"},
    "autoGeneratedDomainNameLabelScope": {"value": "TenantReuse"},
    "sku": {"value": "$SKU"},
    "skuCode": {"value": "$SKU_CODE"},
    "workerSize": {"value": "0"},
    "workerSizeId": {"value": "0"},
    "numberOfWorkers": {"value": "1"},
    "linuxFxVersion": {"value": "$LINUX_FX_VERSION"}
}
EOF

# Fonction de nettoyage
cleanup() {
    rm -f "$PARAM_FILE"
}
trap cleanup EXIT

print_info "Exécution du déploiement ARM..."

if az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --template-file "$TEMPLATE_FILE" \
    --parameters "@$PARAM_FILE"; then
    
    print_success "Déploiement ARM terminé avec succès!"
    
    # Récupération des informations de la Web App
    print_info "Récupération des informations de déploiement..."
    
    WEB_APP_URL=$(az webapp show --name "$WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "defaultHostName" -o tsv)
    WEB_APP_STATE=$(az webapp show --name "$WEB_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "state" -o tsv)
    
    print_success "Informations de la Web App:"
    echo "  • Nom: $WEB_APP_NAME"
    echo "  • URL: https://$WEB_APP_URL"
    echo "  • État: $WEB_APP_STATE"
    echo "  • Groupe de ressources: $RESOURCE_GROUP"
    
    # Configuration post-déploiement
    print_info "Configuration post-déploiement..."
    print_info "Vous pouvez maintenant configurer vos variables d'environnement avec:"
    print_warning "az webapp config appsettings set --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --settings KEY=VALUE"
    
    # Résumé final
    print_success "🎉 Déploiement terminé avec succès!"
    print_info "Prochaines étapes recommandées:"
    echo "1. Configurer les variables d'environnement de votre application"
    echo "2. Déployer votre code via Azure CLI, GitHub Actions, ou VS Code"
    echo "3. Configurer un nom de domaine personnalisé si nécessaire"
    echo "4. Activer Application Insights pour le monitoring"
    
    echo ""
    print_success "🌐 Votre application est accessible à: https://$WEB_APP_URL"
    
else
    print_error "Échec du déploiement ARM"
    exit 1
fi