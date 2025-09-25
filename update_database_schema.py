"""
Script de mise à jour de la base de données Azure SQL
Ajoute les nouvelles colonnes pour supporter les attachements de fichiers
"""

import pyodbc
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def get_azure_sql_connection():
    """Créer une connexion à Azure SQL Database"""
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    driver = os.getenv('AZURE_ODBC_DRIVER', 'ODBC Driver 18 for SQL Server')
    
    connection_string = f"""
        DRIVER={{{driver}}};
        SERVER={server};
        DATABASE={database};
        UID={username};
        PWD={password};
        Encrypt=yes;
        TrustServerCertificate=no;
        Connection Timeout=30;
    """
    
    return pyodbc.connect(connection_string)

def update_database_schema():
    """Mettre à jour le schéma de la base de données"""
    
    print("🔄 Mise à jour du schéma de base de données...")
    print("=" * 60)
    
    try:
        conn = get_azure_sql_connection()
        cursor = conn.cursor()
        
        # Vérifier si les colonnes existent déjà
        check_columns_query = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'incidents' 
        AND COLUMN_NAME IN ('has_attachments', 'attachments_count')
        """
        
        cursor.execute(check_columns_query)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        updates_needed = []
        
        # Ajouter has_attachments si elle n'existe pas
        if 'has_attachments' not in existing_columns:
            updates_needed.append("""
            ALTER TABLE incidents 
            ADD has_attachments BIT DEFAULT 0
            """)
            print("📋 Ajout colonne 'has_attachments'")
        
        # Ajouter attachments_count si elle n'existe pas
        if 'attachments_count' not in existing_columns:
            updates_needed.append("""
            ALTER TABLE incidents 
            ADD attachments_count INT DEFAULT 0
            """)
            print("📋 Ajout colonne 'attachments_count'")
        
        # Exécuter les mises à jour
        for update_sql in updates_needed:
            print(f"🔧 Exécution: {update_sql.strip()}")
            cursor.execute(update_sql)
            conn.commit()
        
        # Créer la table des attachements si elle n'existe pas
        create_attachments_table = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='incident_attachments' AND xtype='U')
        CREATE TABLE incident_attachments (
            id INT IDENTITY(1,1) PRIMARY KEY,
            incident_id INT NOT NULL,
            filename NVARCHAR(255) NOT NULL,
            original_filename NVARCHAR(255) NOT NULL,
            file_path NVARCHAR(500) NOT NULL,
            file_size BIGINT NOT NULL,
            file_type NVARCHAR(100) NOT NULL,
            mime_type NVARCHAR(100),
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        )
        """
        
        print("📋 Création table 'incident_attachments'")
        cursor.execute(create_attachments_table)
        conn.commit()
        
        # Mettre à jour les incidents existants
        update_existing_incidents = """
        UPDATE incidents 
        SET has_attachments = 0, attachments_count = 0 
        WHERE has_attachments IS NULL OR attachments_count IS NULL
        """
        
        print("🔄 Mise à jour des incidents existants")
        cursor.execute(update_existing_incidents)
        conn.commit()
        
        print("✅ Mise à jour du schéma terminée avec succès!")
        print("=" * 60)
        
        # Afficher le schéma mis à jour
        schema_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'incidents'
        ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(schema_query)
        columns = cursor.fetchall()
        
        print("📋 Schéma actuel de la table 'incidents':")
        print("-" * 60)
        for col in columns:
            print(f"  {col[0]:20} | {col[1]:15} | Nullable: {col[2]:3} | Default: {col[3] or 'NULL'}")
        
        print("-" * 60)
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return False

def test_updated_schema():
    """Tester le nouveau schéma"""
    
    print("\n🧪 Test du nouveau schéma...")
    
    try:
        conn = get_azure_sql_connection()
        cursor = conn.cursor()
        
        # Test simple SELECT
        test_query = """
        SELECT TOP 1 id, titre, has_attachments, attachments_count
        FROM incidents
        """
        
        cursor.execute(test_query)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Test réussi - Incident exemple:")
            print(f"   ID: {result[0]}")
            print(f"   Titre: {result[1]}")
            print(f"   Has attachments: {result[2]}")
            print(f"   Attachments count: {result[3]}")
        else:
            print("ℹ️  Aucun incident trouvé (table vide)")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script de mise à jour Azure SQL Database")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    required_vars = ['AZURE_SQL_SERVER', 'AZURE_SQL_DATABASE', 'AZURE_SQL_USERNAME', 'AZURE_SQL_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes: {missing_vars}")
        print("   Vérifiez votre fichier .env")
        exit(1)
    
    # Mettre à jour le schéma
    if update_database_schema():
        # Tester le nouveau schéma
        test_updated_schema()
        print("\n🎉 Mise à jour terminée! Vous pouvez maintenant relancer Flask.")
    else:
        print("\n💥 Échec de la mise à jour. Vérifiez les erreurs ci-dessus.")