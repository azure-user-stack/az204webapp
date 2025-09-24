-- ===============================================
-- Script d'initialisation Azure SQL Database
-- Flask Incidents Réseau - Version Azure
-- ===============================================

-- Vérification de la connexion Azure SQL
PRINT '🔧 Initialisation de la base de données Azure SQL pour Flask Incidents Réseau'
PRINT '📅 Date : ' + CONVERT(varchar, GETDATE(), 120)
PRINT '🌐 Serveur : ' + @@SERVERNAME
PRINT '💾 Base de données : ' + DB_NAME()

-- Création de la table incidents si elle n'existe pas
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='incidents' AND xtype='U')
BEGIN
    PRINT '📋 Création de la table incidents...'
    
    CREATE TABLE incidents (
        id INT IDENTITY(1,1) PRIMARY KEY,
        titre NVARCHAR(200) NOT NULL,
        severite NVARCHAR(50) NOT NULL CHECK (severite IN ('Faible', 'Moyenne', 'Élevée', 'Critique')),
        description NVARCHAR(1000),
        date_incident DATETIME2 NOT NULL DEFAULT GETDATE(),
        date_creation DATETIME2 NOT NULL DEFAULT GETDATE(),
        date_modification DATETIME2 NOT NULL DEFAULT GETDATE()
    )
    
    PRINT '✅ Table incidents créée avec succès !'
END
ELSE
BEGIN
    PRINT '⚠️  Table incidents existe déjà'
END

-- Ajout d'un trigger pour mettre à jour automatiquement date_modification
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'tr_incidents_update_date')
BEGIN
    PRINT '🔄 Création du trigger de mise à jour automatique...'
    
    EXEC ('
    CREATE TRIGGER tr_incidents_update_date
    ON incidents
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON
        UPDATE incidents 
        SET date_modification = GETDATE()
        FROM incidents i
        INNER JOIN inserted ins ON i.id = ins.id
    END
    ')
    
    PRINT '✅ Trigger créé avec succès !'
END

-- Vérification et insertion des données d'exemple
DECLARE @count INT
SELECT @count = COUNT(*) FROM incidents

IF @count = 0
BEGIN
    PRINT '📊 Insertion des données d''exemple...'
    
    INSERT INTO incidents (titre, severite, description, date_incident) VALUES
    ('Panne réseau principal Azure', 'Critique', 'Interruption complète de la connectivité réseau entre les centres de données Azure. Impact sur tous les services cloud. Équipes techniques mobilisées pour diagnostic urgent.', DATEADD(hour, -2, GETDATE())),
    
    ('Latence élevée base de données', 'Élevée', 'Temps de réponse anormalement élevé sur les requêtes SQL Azure. Performances dégradées pour les applications métier. Investigation en cours sur l''indexation et les ressources allouées.', DATEADD(hour, -8, GETDATE())),
    
    ('Certificat SSL expiré', 'Moyenne', 'Le certificat SSL du domaine principal a expiré cette nuit. Les connexions HTTPS sont impactées. Procédure de renouvellement en cours avec l''autorité de certification.', DATEADD(day, -1, GETDATE())),
    
    ('Mise à jour sécurité planifiée', 'Faible', 'Installation des correctifs de sécurité sur les serveurs Azure pendant la fenêtre de maintenance. Redémarrage programmé des services non critiques prévu dans 2 heures.', DATEADD(minute, -30, GETDATE())),
    
    ('Problème DNS intermittent', 'Moyenne', 'Résolution DNS défaillante par intermittence pour certains sous-domaines. Impact sur l''accessibilité de quelques services web. Configuration DNS en cours de vérification.', DATEADD(hour, -4, GETDATE()))
    
    PRINT '✅ ' + CAST(@@ROWCOUNT AS VARCHAR(10)) + ' incidents d''exemple insérés !'
END
ELSE
BEGIN
    PRINT '⚠️  La table contient déjà ' + CAST(@count AS VARCHAR(10)) + ' incidents'
END

-- Vérification des données insérées
PRINT '📊 Vérification des données...'
SELECT 
    COUNT(*) as [Total Incidents],
    SUM(CASE WHEN severite = 'Critique' THEN 1 ELSE 0 END) as [Critiques],
    SUM(CASE WHEN severite = 'Élevée' THEN 1 ELSE 0 END) as [Élevées],
    SUM(CASE WHEN severite = 'Moyenne' THEN 1 ELSE 0 END) as [Moyennes],
    SUM(CASE WHEN severite = 'Faible' THEN 1 ELSE 0 END) as [Faibles]
FROM incidents

-- Affichage des incidents récents
PRINT '📋 Derniers incidents enregistrés :'
SELECT TOP 3
    id,
    titre,
    severite,
    FORMAT(date_incident, 'dd/MM/yyyy HH:mm') as [Date Incident]
FROM incidents
ORDER BY date_creation DESC

-- Création d'un index pour optimiser les performances
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_incidents_date_severite')
BEGIN
    PRINT '🔍 Création de l''index de performance...'
    CREATE NONCLUSTERED INDEX IX_incidents_date_severite
    ON incidents (date_incident DESC, severite)
    INCLUDE (titre, description)
    
    PRINT '✅ Index créé pour optimiser les requêtes !'
END

-- Statistiques finales
PRINT ''
PRINT '🎉 ==============================================='
PRINT '   Initialisation Azure SQL Database terminée !'
PRINT '==============================================='
PRINT '📊 Base de données : ' + DB_NAME()
PRINT '📋 Table incidents : OK'
PRINT '🔄 Trigger mise à jour : OK'
PRINT '🔍 Index performance : OK'
PRINT '📊 Données exemple : ' + CAST((SELECT COUNT(*) FROM incidents) AS VARCHAR(10)) + ' incidents'
PRINT ''
PRINT '🚀 Votre application Flask peut maintenant se connecter à Azure SQL Database !'
PRINT '   Utilisez les variables d''environnement pour la connexion.'

-- Script de vérification de connexion Flask (commenté pour information)
/*
Variables d'environnement requises pour Flask :
AZURE_SQL_SERVER=votre-serveur.database.windows.net
AZURE_SQL_DATABASE=votre-base-de-donnees  
AZURE_SQL_USERNAME=votre-utilisateur
AZURE_SQL_PASSWORD=votre-mot-de-passe

Chaîne de connexion générée :
mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30
*/