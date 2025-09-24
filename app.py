from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import urllib.parse
import os
from sqlalchemy import text

# Charger les variables d'environnement depuis le fichier .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Variables d'environnement chargées depuis .env")
except ImportError:
    print("⚠️  python-dotenv non installé, utilisation des variables système uniquement")

app = Flask(__name__)

# ========================================
# CONFIGURATION AZURE SQL DATABASE
# ========================================

# 🌐 Configuration Azure SQL Database
# Modifiez ces paramètres selon votre Azure SQL Database
AZURE_SQL_SERVER = os.environ.get('AZURE_SQL_SERVER', 'votre-serveur.database.windows.net')
AZURE_SQL_DATABASE = os.environ.get('AZURE_SQL_DATABASE', 'IncidentsReseau')
AZURE_SQL_USERNAME = os.environ.get('AZURE_SQL_USERNAME', 'votre-admin')
AZURE_SQL_PASSWORD = os.environ.get('AZURE_SQL_PASSWORD', 'VotreMotDePasse123!')

# 🔐 Méthodes d'authentification Azure SQL
def create_azure_connection_string():
    """Créer la chaîne de connexion Azure SQL Database"""
    
    # Récupérer la configuration depuis les variables d'environnement
    odbc_driver = os.environ.get('AZURE_ODBC_DRIVER', 'ODBC Driver 18 for SQL Server')
    encrypt = os.environ.get('AZURE_ENCRYPT', 'yes')
    trust_cert = os.environ.get('AZURE_TRUST_SERVER_CERTIFICATE', 'no')
    timeout = os.environ.get('AZURE_CONNECTION_TIMEOUT', '30')
    
    # Option 1: Authentification SQL Server (classique)
    if AZURE_SQL_USERNAME and AZURE_SQL_PASSWORD:
        print("🔐 Utilisation de l'authentification SQL Server pour Azure")
        connection_params = urllib.parse.quote_plus(
            f"DRIVER={{{odbc_driver}}};"
            f"SERVER={AZURE_SQL_SERVER};"
            f"DATABASE={AZURE_SQL_DATABASE};"
            f"UID={AZURE_SQL_USERNAME};"
            f"PWD={AZURE_SQL_PASSWORD};"
            f"Encrypt={encrypt};"                    # Configuration depuis .env
            f"TrustServerCertificate={trust_cert};"  # Configuration depuis .env
            f"Connection Timeout={timeout};"
        )
    else:
        # Option 2: Azure Active Directory (pour plus tard)
        print("⚠️  Variables d'environnement manquantes pour Azure SQL")
        raise ValueError("Configuration Azure SQL incomplète")
    
    return f"mssql+pyodbc:///?odbc_connect={connection_params}"

# Configuration Flask
app.config['SQLALCHEMY_DATABASE_URI'] = create_azure_connection_string()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'azure-secret-key-dev')

# Initialisation SQLAlchemy
db = SQLAlchemy(app)

# ========================================
# MODÈLE DE DONNÉES (identique au projet original)
# ========================================

class Incident(db.Model):
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    severite = db.Column(db.String(50), nullable=False)
    date_incident = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Incident {self.id}: {self.titre}>'
    
    def to_dict(self):
        """Convertir en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'titre': self.titre,
            'severite': self.severite,
            'date_incident': self.date_incident.strftime('%Y-%m-%d %H:%M')
        }

# ========================================
# ROUTES PRINCIPALES (adaptées du projet original)
# ========================================

@app.route('/')
def index():
    """Page principale avec liste des incidents"""
    try:
        incidents = Incident.query.order_by(Incident.date_incident.desc()).all()
        return render_template('incidents.html', incidents=incidents)
    except Exception as e:
        flash(f'Erreur de connexion à Azure SQL Database: {str(e)}', 'error')
        # Fallback avec des données par défaut si la DB n'est pas accessible
        incidents_demo = [
            {'id': 1, 'titre': 'Connexion Azure en cours...', 'severite': 'Info', 'date_incident': datetime.now()}
        ]
        return render_template('incidents.html', incidents=incidents_demo)

@app.route('/ajouter')
def ajouter_incident_form():
    """Formulaire d'ajout d'incident"""
    return render_template('ajouter.html')

@app.route('/ajouter-incident', methods=['POST'])
def ajouter_incident():
    """Traitement de l'ajout d'incident"""
    try:
        titre = request.form.get('titre', '').strip()
        severite = request.form.get('severite', 'Moyenne')
        
        if not titre:
            flash('Le titre de l\'incident est obligatoire', 'error')
            return redirect(url_for('ajouter_incident_form'))
        
        # Créer le nouvel incident
        nouvel_incident = Incident(
            titre=titre,
            severite=severite,
            date_incident=datetime.now()
        )
        
        # Sauvegarder dans Azure SQL
        db.session.add(nouvel_incident)
        db.session.commit()
        
        flash(f'Incident "{titre}" ajouté avec succès dans Azure SQL Database!', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'ajout dans Azure SQL: {str(e)}', 'error')
        return redirect(url_for('ajouter_incident_form'))

@app.route('/incident/<int:incident_id>')
def detail_incident(incident_id):
    """Page de détail d'un incident"""
    try:
        incident = Incident.query.get_or_404(incident_id)
        return render_template('detail.html', incident=incident)
    except Exception as e:
        flash(f'Erreur lors de la récupération de l\'incident: {str(e)}', 'error')
        return redirect(url_for('index'))

# ========================================
# API REST (pour intégrations)
# ========================================

@app.route('/api/incidents')
def api_incidents():
    """API REST - Liste des incidents"""
    try:
        incidents = Incident.query.order_by(Incident.date_incident.desc()).all()
        return jsonify([incident.to_dict() for incident in incidents])
    except Exception as e:
        return jsonify({'error': f'Erreur Azure SQL: {str(e)}'}), 500

@app.route('/api/incidents/<int:incident_id>')
def api_incident_detail(incident_id):
    """API REST - Détail d'un incident"""
    try:
        incident = Incident.query.get_or_404(incident_id)
        return jsonify(incident.to_dict())
    except Exception as e:
        return jsonify({'error': f'Erreur Azure SQL: {str(e)}'}), 500

# ========================================
# ROUTES DE DIAGNOSTIC AZURE
# ========================================

@app.route('/azure-status')
def azure_status():
    """Page de diagnostic de la connexion Azure SQL"""
    try:
        # Test de connexion Azure SQL
        result = db.session.execute(text("""
            SELECT 
                @@SERVERNAME as serveur_azure,
                DB_NAME() as base_donnees,
                SYSTEM_USER as utilisateur_azure,
                @@VERSION as version_sql,
                GETDATE() as heure_azure
        """))
        
        info = result.fetchone()
        
        # Compter les incidents
        count_incidents = db.session.execute(text("SELECT COUNT(*) FROM incidents")).fetchone()[0]
        
        azure_info = {
            'status': 'Connecté à Azure SQL Database',
            'serveur': info[0],
            'base_donnees': info[1], 
            'utilisateur': info[2],
            'version_sql': info[3][:100] + '...',
            'heure_serveur': info[4].strftime('%Y-%m-%d %H:%M:%S'),
            'nombre_incidents': count_incidents,
            'region_azure': 'Détection automatique...'
        }
        
        return jsonify(azure_info)
        
    except Exception as e:
        return jsonify({
            'status': 'Erreur de connexion',
            'erreur': str(e),
            'configuration': {
                'serveur': AZURE_SQL_SERVER,
                'base': AZURE_SQL_DATABASE,
                'utilisateur': AZURE_SQL_USERNAME
            }
        }), 500

@app.route('/test-azure')
def test_azure():
    """Page de test Azure SQL Database"""
    try:
        # Tests de base
        db.session.execute(text("SELECT 1"))
        
        return jsonify({
            'azure_sql_test': 'SUCCESS',
            'message': 'Connexion Azure SQL Database fonctionnelle',
            'server': AZURE_SQL_SERVER,
            'database': AZURE_SQL_DATABASE
        })
        
    except Exception as e:
        return jsonify({
            'azure_sql_test': 'FAILED', 
            'error': str(e)
        }), 500

# ========================================
# INITIALISATION ET LANCEMENT
# ========================================

def init_azure_database():
    """Initialiser la base de données Azure SQL si nécessaire"""
    try:
        with app.app_context():
            # Créer les tables si elles n'existent pas
            db.create_all()
            
            # Vérifier s'il y a déjà des données
            existing_count = Incident.query.count()
            
            if existing_count == 0:
                print("📊 Initialisation des données de démonstration dans Azure SQL...")
                
                # Données initiales (identiques au projet original)
                incidents_demo = [
                    Incident(titre='Panne serveur principal Azure', severite='Critique', 
                            date_incident=datetime(2025, 9, 20, 14, 30)),
                    Incident(titre='Latence élevée réseau Azure', severite='Moyenne',
                            date_incident=datetime(2025, 9, 21, 9, 15)), 
                    Incident(titre='Connexion intermittente Azure', severite='Faible',
                            date_incident=datetime(2025, 9, 22, 16, 45)),
                    Incident(titre='Échec authentification Azure AD', severite='Élevée',
                            date_incident=datetime(2025, 9, 23, 8, 20)),
                    Incident(titre='Surcharge bande passante Azure', severite='Moyenne',
                            date_incident=datetime(2025, 9, 23, 11, 10))
                ]
                
                for incident in incidents_demo:
                    db.session.add(incident)
                
                db.session.commit()
                print(f"✅ {len(incidents_demo)} incidents ajoutés dans Azure SQL Database")
            else:
                print(f"📊 Azure SQL Database contient déjà {existing_count} incidents")
                
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation Azure SQL: {e}")

if __name__ == '__main__':
    print("🚀 Démarrage Flask - Incidents Réseau avec Azure SQL Database")
    print("=" * 60)
    print(f"☁️  Serveur Azure SQL: {AZURE_SQL_SERVER}")
    print(f"💾 Base de données: {AZURE_SQL_DATABASE}")
    print(f"👤 Utilisateur: {AZURE_SQL_USERNAME}")
    print("=" * 60)
    print("📋 Routes disponibles:")
    print("   📊 / - Liste des incidents")
    print("   ➕ /ajouter - Ajouter un incident")
    print("   🔍 /incident/<id> - Détail d'un incident")
    print("   🧪 /azure-status - Diagnostic Azure SQL")
    print("   🔬 /test-azure - Test de connexion")
    print("   📡 /api/incidents - API REST")
    print("=" * 60)
    
    # Initialisation de la base de données Azure
    init_azure_database()
    
    # Démarrage de l'application sur port 5003 pour éviter les conflits
    print("🌐 Application accessible sur: http://localhost:5003")
    app.run(host='0.0.0.0', port=5003, debug=True)