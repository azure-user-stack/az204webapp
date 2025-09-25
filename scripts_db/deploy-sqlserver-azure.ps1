# Script de déploiement SQL Server sur Azure
# Auteur: Azure DevOps Team
# Date: 2025-09-24

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$ServerName,
    
    [Parameter(Mandatory=$true)]
    [string]$DatabaseName,
    
    [Parameter(Mandatory=$true)]
    [string]$Location = "East US",
    
    [Parameter(Mandatory=$true)]
    [string]$AdminUsername,
    
    [Parameter(Mandatory=$true)]
    [SecureString]$AdminPassword,
    
    [string]$ServiceTier = "Basic",
    [string]$ComputeModel = "Provisioned",
    [string]$ComputeSize = "Basic"
)

Write-Host "=== Déploiement SQL Server sur Azure ===" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName"
Write-Host "Server Name: $ServerName"
Write-Host "Database Name: $DatabaseName"
Write-Host "Location: $Location"
Write-Host ""

try {
    # Vérifier si Azure CLI est installé
    Write-Host "Vérification d'Azure CLI..." -ForegroundColor Yellow
    az --version
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI n'est pas installé ou n'est pas accessible."
    }

    # Se connecter à Azure (si nécessaire)
    Write-Host "Vérification de la connexion Azure..." -ForegroundColor Yellow
    $account = az account show --query "user.name" -o tsv 2>$null
    if (-not $account) {
        Write-Host "Connexion à Azure requise..." -ForegroundColor Yellow
        az login
    } else {
        Write-Host "Connecté en tant que: $account" -ForegroundColor Green
    }

    # Créer le groupe de ressources s'il n'existe pas
    Write-Host "Création/Vérification du groupe de ressources..." -ForegroundColor Yellow
    az group create --name $ResourceGroupName --location $Location
    if ($LASTEXITCODE -ne 0) {
        throw "Échec de la création du groupe de ressources"
    }

    # Convertir SecureString en texte brut pour Azure CLI
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword))

    # Créer le serveur SQL Server
    Write-Host "Création du serveur SQL Server..." -ForegroundColor Yellow
    az sql server create `
        --resource-group $ResourceGroupName `
        --name $ServerName `
        --location $Location `
        --admin-user $AdminUsername `
        --admin-password $plainPassword
    
    if ($LASTEXITCODE -ne 0) {
        throw "Échec de la création du serveur SQL"
    }

    # Configurer les règles de pare-feu
    Write-Host "Configuration des règles de pare-feu..." -ForegroundColor Yellow
    
    # Autoriser les services Azure
    az sql server firewall-rule create `
        --resource-group $ResourceGroupName `
        --server $ServerName `
        --name "AllowAzureServices" `
        --start-ip-address 0.0.0.0 `
        --end-ip-address 0.0.0.0

    # Autoriser l'IP locale (optionnel)
    $localIP = (Invoke-RestMethod -Uri "https://ipinfo.io/ip").Trim()
    Write-Host "Configuration de l'accès pour l'IP locale: $localIP" -ForegroundColor Yellow
    az sql server firewall-rule create `
        --resource-group $ResourceGroupName `
        --server $ServerName `
        --name "AllowLocalIP" `
        --start-ip-address $localIP `
        --end-ip-address $localIP

    # Créer la base de données
    Write-Host "Création de la base de données..." -ForegroundColor Yellow
    az sql db create `
        --resource-group $ResourceGroupName `
        --server $ServerName `
        --name $DatabaseName `
        --service-objective $ServiceTier
    
    if ($LASTEXITCODE -ne 0) {
        throw "Échec de la création de la base de données"
    }

    # Obtenir la chaîne de connexion
    Write-Host "Récupération des informations de connexion..." -ForegroundColor Yellow
    $connectionString = "Server=tcp:$ServerName.database.windows.net,1433;Initial Catalog=$DatabaseName;Persist Security Info=False;User ID=$AdminUsername;Password=***;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
    
    Write-Host ""
    Write-Host "=== DÉPLOIEMENT RÉUSSI ===" -ForegroundColor Green
    Write-Host "Serveur SQL: $ServerName.database.windows.net" -ForegroundColor Green
    Write-Host "Base de données: $DatabaseName" -ForegroundColor Green
    Write-Host "Chaîne de connexion (sans mot de passe):" -ForegroundColor Yellow
    Write-Host $connectionString -ForegroundColor Cyan
    Write-Host ""
    Write-Host "N'oubliez pas de configurer votre fichier .env avec ces informations!" -ForegroundColor Yellow

} catch {
    Write-Host ""
    Write-Host "=== ERREUR DE DÉPLOIEMENT ===" -ForegroundColor Red
    Write-Host "Erreur: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Script terminé avec succès!" -ForegroundColor Green