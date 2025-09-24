"""
🧪 Test de connexion rapide Azure SQL Database
Flask Incidents Réseau - Version Azure

Script léger pour tester rapidement la connexion à Azure SQL Database
"""

import os
import sys
import time
from datetime import datetime

# Charger les variables d'environnement depuis le fichier .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Variables d'environnement chargées depuis .env")
except ImportError:
    print("⚠️  python-dotenv non installé, utilisation des variables système uniquement")
    print("   Installez avec: pip install python-dotenv")

def test_quick_connection():
    """Test de connexion rapide"""
    print("🧪 TEST RAPIDE DE CONNEXION AZURE SQL DATABASE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Vérification des variables d'environnement
    print("🔍 Vérification des variables d'environnement...")
    
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    if not all([server, database, username, password]):
        print("❌ Variables d'environnement manquantes !")
        print("   Définissez: AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USERNAME, AZURE_SQL_PASSWORD")
        return False
    
    print(f"✅ Serveur: {server}")
    print(f"✅ Base: {database}")
    print(f"✅ Utilisateur: {username}")
    print()
    
    # Test d'import des modules
    print("📦 Vérification des modules Python...")
    try:
        import pyodbc
        print("✅ pyodbc importé")
    except ImportError:
        print("❌ pyodbc non installé: pip install pyodbc")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        print("✅ sqlalchemy importé")
    except ImportError:
        print("❌ sqlalchemy non installé: pip install SQLAlchemy==1.4.53")
        return False
    
    print()
    
    # Test de connexion
    print("🔌 Test de connexion...")
    
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
        f"&Encrypt=yes"
        f"&TrustServerCertificate=no"
        f"&Connection+Timeout=30"
    )
    
    try:
        start_time = time.time()
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Test de requête simple
            result = conn.execute(text("SELECT GETDATE(), @@VERSION"))
            row = result.fetchone()
            
            connection_time = time.time() - start_time
            
            print(f"✅ Connexion réussie en {connection_time:.2f}s")
            print(f"🕒 Heure serveur: {row[0]}")
            print(f"📊 Version: {row[1][:50]}...")
            print()
            
            # Test de la table incidents
            print("📋 Test de la table incidents...")
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM incidents"))
                count = result.scalar()
                print(f"✅ Table incidents trouvée avec {count} enregistrement(s)")
                
                if count > 0:
                    result = conn.execute(text("""
                        SELECT TOP 1 id, titre, severite 
                        FROM incidents 
                        ORDER BY date_incident DESC
                    """))
                    latest = result.fetchone()
                    print(f"📄 Dernier incident: #{latest[0]} - {latest[1]} ({latest[2]})")
                
            except Exception as e:
                if "Invalid object name 'incidents'" in str(e):
                    print("⚠️  Table 'incidents' non trouvée - exécutez init_azure_database.sql")
                else:
                    print(f"❌ Erreur sur la table incidents: {e}")
            
            print()
            print("🎉 TEST RÉUSSI ! Votre configuration Azure SQL fonctionne.")
            print("🚀 Vous pouvez lancer l'application: python app.py")
            return True
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("🔧 Solutions possibles:")
        print("   1. Vérifiez vos identifiants Azure SQL")
        print("   2. Contrôlez les règles de pare-feu Azure")
        print("   3. Installez ODBC Driver 18 for SQL Server")
        print("   4. Vérifiez votre connexion internet")
        return False

if __name__ == "__main__":
    try:
        success = test_quick_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)