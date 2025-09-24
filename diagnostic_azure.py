"""
🔧 Diagnostic complet Azure SQL Database
Flask Incidents Réseau - Version Azure

Ce script effectue tous les tests de diagnostic pour Azure SQL Database
"""

import os
import sys
import time
import pyodbc
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Charger les variables d'environnement depuis le fichier .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Variables d'environnement chargées depuis .env")
except ImportError:
    print("⚠️  python-dotenv non installé, utilisation des variables système uniquement")

def print_banner():
    """Affiche la bannière de diagnostic"""
    print("=" * 80)
    print("🔧 DIAGNOSTIC AZURE SQL DATABASE")
    print("Flask Incidents Réseau - Version Cloud Azure")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"💻 OS: {os.name}")
    print("=" * 80)

def check_environment_variables():
    """Vérifie les variables d'environnement"""
    print("🔍 1. VÉRIFICATION DES VARIABLES D'ENVIRONNEMENT")
    print("-" * 50)
    
    required_vars = {
        'AZURE_SQL_SERVER': 'Serveur Azure SQL',
        'AZURE_SQL_DATABASE': 'Base de données',
        'AZURE_SQL_USERNAME': 'Nom d\'utilisateur',
        'AZURE_SQL_PASSWORD': 'Mot de passe'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if var == 'AZURE_SQL_PASSWORD':
                print(f"✅ {description}: {'*' * len(value)}")
            else:
                print(f"✅ {description}: {value}")
        else:
            print(f"❌ {description}: MANQUANT")
            missing_vars.append(var)
    
    print()
    return len(missing_vars) == 0, missing_vars

def check_pyodbc_drivers():
    """Vérifie les drivers ODBC disponibles"""
    print("🔍 2. VÉRIFICATION DES DRIVERS ODBC")
    print("-" * 50)
    
    try:
        drivers = pyodbc.drivers()
        print(f"📊 {len(drivers)} driver(s) ODBC trouvé(s):")
        
        for i, driver in enumerate(drivers, 1):
            print(f"   {i}. {driver}")
        
        # Vérifier la présence du driver SQL Server
        sql_server_drivers = [d for d in drivers if 'SQL Server' in d]
        
        if sql_server_drivers:
            print(f"\n✅ Driver SQL Server disponible: {sql_server_drivers[0]}")
            return True, sql_server_drivers[0]
        else:
            print("\n❌ Aucun driver SQL Server trouvé")
            return False, None
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des drivers: {e}")
        return False, None

def test_basic_connection():
    """Test de connexion basique avec pyodbc"""
    print("🔍 3. TEST DE CONNEXION BASIQUE (pyodbc)")
    print("-" * 50)
    
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )
    
    try:
        print(f"📡 Tentative de connexion à {server}...")
        start_time = time.time()
        
        conn = pyodbc.connect(connection_string)
        connection_time = time.time() - start_time
        
        print(f"✅ Connexion réussie en {connection_time:.2f}s")
        
        # Test d'une requête simple
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        print(f"📊 Version SQL Server: {version[:80]}...")
        
        # Test de performance
        cursor.execute("SELECT GETDATE()")
        current_time = cursor.fetchone()[0]
        print(f"🕒 Heure serveur: {current_time}")
        
        cursor.close()
        conn.close()
        
        return True, connection_time
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False, 0

def test_sqlalchemy_connection():
    """Test de connexion avec SQLAlchemy"""
    print("🔍 4. TEST DE CONNEXION SQLALCHEMY")
    print("-" * 50)
    
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
        f"&Encrypt=yes"
        f"&TrustServerCertificate=no"
        f"&Connection+Timeout=30"
    )
    
    try:
        print("📡 Création du moteur SQLAlchemy...")
        engine = create_engine(connection_string, echo=False)
        
        start_time = time.time()
        with engine.connect() as conn:
            connection_time = time.time() - start_time
            
            print(f"✅ Connexion SQLAlchemy réussie en {connection_time:.2f}s")
            
            # Test des métadonnées
            result = conn.execute(text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"))
            table_count = result.scalar()
            print(f"📊 Nombre de tables: {table_count}")
            
            # Test de la table incidents
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM incidents"))
                incident_count = result.scalar()
                print(f"📋 Nombre d'incidents: {incident_count}")
            except:
                print("⚠️  Table 'incidents' non trouvée (normale si pas encore initialisée)")
        
        return True, connection_time
        
    except SQLAlchemyError as e:
        print(f"❌ Erreur SQLAlchemy: {e}")
        return False, 0
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False, 0

def test_azure_connectivity():
    """Test de connectivité réseau vers Azure"""
    print("🔍 5. TEST DE CONNECTIVITÉ RÉSEAU AZURE")
    print("-" * 50)
    
    server = os.getenv('AZURE_SQL_SERVER')
    
    if not server:
        print("❌ Serveur Azure non configuré")
        return False
    
    # Extraire le nom du serveur sans le port
    server_name = server.split('.')[0] if '.' in server else server
    
    try:
        import socket
        
        print(f"🌐 Test de résolution DNS: {server}")
        
        # Résolution DNS
        start_time = time.time()
        ip_address = socket.gethostbyname(server.split(',')[0])  # Enlever le port si présent
        dns_time = time.time() - start_time
        
        print(f"✅ Résolution DNS réussie en {dns_time:.3f}s")
        print(f"📍 Adresse IP: {ip_address}")
        
        # Test de connexion TCP sur le port 1433
        print(f"🔌 Test de connexion TCP sur le port 1433...")
        
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((server.split(',')[0], 1433))
        tcp_time = time.time() - start_time
        sock.close()
        
        if result == 0:
            print(f"✅ Connexion TCP réussie en {tcp_time:.3f}s")
            return True
        else:
            print(f"❌ Connexion TCP échouée (code: {result})")
            return False
            
    except socket.gaierror as e:
        print(f"❌ Erreur de résolution DNS: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connectivité: {e}")
        return False

def test_database_operations():
    """Test des opérations de base de données"""
    print("🔍 6. TEST DES OPÉRATIONS DE BASE DE DONNÉES")
    print("-" * 50)
    
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
        f"&Encrypt=yes"
        f"&TrustServerCertificate=no"
        f"&Connection+Timeout=30"
    )
    
    try:
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Test 1: Lecture des métadonnées
            print("📊 Test 1: Lecture des métadonnées...")
            result = conn.execute(text("""
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """))
            
            tables = result.fetchall()
            print(f"   ✅ {len(tables)} table(s) trouvée(s)")
            
            for table in tables:
                print(f"      📋 {table[1]} (Schéma: {table[0]})")
            
            # Test 2: Vérification de la table incidents
            print("\n📋 Test 2: Vérification table incidents...")
            try:
                result = conn.execute(text("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'incidents'
                    ORDER BY ORDINAL_POSITION
                """))
                
                columns = result.fetchall()
                if columns:
                    print(f"   ✅ Table incidents trouvée avec {len(columns)} colonnes:")
                    for col in columns:
                        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                        print(f"      📄 {col[0]} ({col[1]}) - {nullable}")
                else:
                    print("   ⚠️  Table incidents non trouvée")
                
                # Test 3: Lecture des données
                print("\n📊 Test 3: Lecture des données incidents...")
                result = conn.execute(text("SELECT COUNT(*) FROM incidents"))
                count = result.scalar()
                print(f"   ✅ {count} incident(s) dans la base")
                
                if count > 0:
                    result = conn.execute(text("""
                        SELECT TOP 3 
                            id, 
                            titre, 
                            severite,
                            date_incident
                        FROM incidents 
                        ORDER BY date_incident DESC
                    """))
                    
                    recent_incidents = result.fetchall()
                    print("   📋 Derniers incidents:")
                    for inc in recent_incidents:
                        print(f"      🔸 #{inc[0]}: {inc[1]} ({inc[2]})")
                
            except Exception as e:
                print(f"   ❌ Erreur sur la table incidents: {e}")
            
            print("\n✅ Tests d'opérations de base de données terminés")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors des tests de base de données: {e}")
        return False

def generate_report(results):
    """Génère un rapport de diagnostic"""
    print("\n" + "=" * 80)
    print("📊 RAPPORT DE DIAGNOSTIC")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    print(f"🎯 Tests réussis: {passed_tests}/{total_tests}")
    print(f"📊 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
    print()
    
    for test_name, result in results.items():
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"   {status}: {test_name}")
    
    print("\n" + "=" * 80)
    
    if passed_tests == total_tests:
        print("🎉 DIAGNOSTIC COMPLET: Votre configuration Azure SQL est opérationnelle !")
        print("🚀 Vous pouvez lancer l'application Flask avec: python app.py")
    else:
        print("⚠️  DIAGNOSTIC PARTIEL: Certains tests ont échoué")
        print("🔧 Consultez les détails ci-dessus pour résoudre les problèmes")
    
    print("=" * 80)

def main():
    """Fonction principale de diagnostic"""
    print_banner()
    
    results = {}
    
    # Test 1: Variables d'environnement
    env_ok, missing_vars = check_environment_variables()
    results["Variables d'environnement"] = env_ok
    
    if not env_ok:
        print(f"\n❌ Variables manquantes: {', '.join(missing_vars)}")
        print("🔧 Configurez ces variables avant de continuer")
        print("=" * 80)
        return
    
    print()
    
    # Test 2: Drivers ODBC
    drivers_ok, driver = check_pyodbc_drivers()
    results["Drivers ODBC"] = drivers_ok
    print()
    
    if not drivers_ok:
        print("❌ Installez ODBC Driver 18 for SQL Server avant de continuer")
        print("=" * 80)
        return
    
    # Test 3: Connectivité réseau
    network_ok = test_azure_connectivity()
    results["Connectivité réseau"] = network_ok
    print()
    
    # Test 4: Connexion basique
    basic_ok, basic_time = test_basic_connection()
    results["Connexion pyodbc"] = basic_ok
    print()
    
    # Test 5: Connexion SQLAlchemy
    sqlalchemy_ok, sqlalchemy_time = test_sqlalchemy_connection()
    results["Connexion SQLAlchemy"] = sqlalchemy_ok
    print()
    
    # Test 6: Opérations de base de données
    if basic_ok and sqlalchemy_ok:
        operations_ok = test_database_operations()
        results["Opérations de base de données"] = operations_ok
        print()
    else:
        results["Opérations de base de données"] = False
    
    # Génération du rapport final
    generate_report(results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Diagnostic interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()