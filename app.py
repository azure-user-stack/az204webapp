from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import urllib.parse
import os
import uuid
import mimetypes
import json
from sqlalchemy import text
from werkzeug.utils import secure_filename

# Azure Queue Storage
try:
    from azure.storage.queue import QueueServiceClient, QueueClient
    AZURE_QUEUE_AVAILABLE = True
    print("✅ Module Azure Storage Queue disponible")
except ImportError:
    AZURE_QUEUE_AVAILABLE = False
    print("⚠️ Module Azure Storage Queue non disponible")
    QueueServiceClient = None
    QueueClient = None

# Charger les variables d'environnement depuis le fichier .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("🔧 Variables d'environnement chargées depuis .env")
except ImportError:
    print("⚠️  python-dotenv non installé, utilisation des variables système uniquement")

app = Flask(__name__)

# ========================================
# CONFIGURATION AZURE QUEUE STORAGE
# ========================================

AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_QUEUE_NAME = os.environ.get('AZURE_QUEUE_NAME', 'incidents-queue')

# Initialisation du client Queue Storage
queue_client = None
if AZURE_QUEUE_AVAILABLE and AZURE_STORAGE_CONNECTION_STRING:
    try:
        queue_service_client = QueueServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        queue_client = queue_service_client.get_queue_client(AZURE_QUEUE_NAME)
        
        # Créer la queue si elle n'existe pas
        queue_client.create_queue()
        print(f"✅ Queue Azure '{AZURE_QUEUE_NAME}' initialisée")
    except Exception as e:
        print(f"⚠️ Erreur initialisation Queue Azure: {e}")
        queue_client = None
else:
    print("⚠️ Azure Queue Storage non configuré - fonctionnalité désactivée")

def send_to_azure_queue(incident_data, message_type="incident"):
    """Envoyer un message vers Azure Queue Storage"""
    if not queue_client:
        print(f"⚠️ Queue Azure non disponible pour {message_type}")
        return False
    
    try:
        message = {
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "data": incident_data
        }
        
        # Encoder le message en JSON puis en base64
        import base64
        message_json = json.dumps(message, ensure_ascii=False, default=str)
        message_b64 = base64.b64encode(message_json.encode('utf-8')).decode('utf-8')
        
        # Envoyer le message
        queue_client.send_message(message_b64)
        print(f"✅ Message {message_type} envoyé vers Azure Queue")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi vers Azure Queue: {e}")
        return False

# ========================================
# CONFIGURATION FLASK ET UPLOAD
# ========================================

# Configuration pour les uploads de fichiers
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'zip', 'rar', '7z', 'log', 'csv', 'json', 'xml'
}

# Créer le dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Vérifier si l'extension du fichier est autorisée"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
    description = db.Column(db.Text)
    date_incident = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Support des fichiers joints
    has_attachments = db.Column(db.Boolean, default=False)
    attachments_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Incident {self.id}: {self.titre}>'
    
    def to_dict(self):
        """Convertir en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'titre': self.titre,
            'severite': self.severite,
            'description': self.description,
            'date_incident': self.date_incident.strftime('%Y-%m-%d %H:%M'),
            'has_attachments': self.has_attachments,
            'attachments_count': self.attachments_count
        }

# Modèle pour les fichiers joints
class IncidentAttachment(db.Model):
    __tablename__ = 'incident_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relation avec l'incident
    incident = db.relationship('Incident', backref=db.backref('attachments', lazy=True))
    
    def __repr__(self):
        return f'<IncidentAttachment {self.id}: {self.original_filename}>'
    
    def to_dict(self):
        """Convertir en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'upload_date': self.upload_date.strftime('%Y-%m-%d %H:%M')
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
    """Traitement de l'ajout d'incident avec support des fichiers joints"""
    try:
        # Récupérer les données du formulaire
        titre = request.form.get('titre', '').strip()
        severite = request.form.get('severite', 'Moyenne')
        description = request.form.get('description', '').strip()
        
        if not titre:
            flash('Le titre de l\'incident est obligatoire', 'error')
            return redirect(url_for('ajouter_incident_form'))
        
        # Créer le nouvel incident
        nouvel_incident = Incident(
            titre=titre,
            severite=severite,
            description=description if description else None,
            date_incident=datetime.now(),
            has_attachments=False,
            attachments_count=0
        )
        
        # Sauvegarder dans Azure SQL pour obtenir l'ID
        db.session.add(nouvel_incident)
        db.session.flush()  # Pour obtenir l'ID sans commit
        
        # Traiter les fichiers joints s'il y en a
        uploaded_files = request.files.getlist('attachments')
        attachments_saved = 0
        
        if uploaded_files and uploaded_files[0].filename:  # Vérifier qu'il y a bien des fichiers
            # Créer un dossier spécifique pour cet incident
            incident_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'incident_{nouvel_incident.id}')
            os.makedirs(incident_folder, exist_ok=True)
            
            for file in uploaded_files:
                if file.filename and allowed_file(file.filename):
                    try:
                        # Sécuriser le nom de fichier
                        original_filename = secure_filename(file.filename)
                        
                        # Créer un nom unique pour éviter les conflits
                        file_extension = os.path.splitext(original_filename)[1]
                        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
                        
                        # Chemin complet du fichier
                        file_path = os.path.join(incident_folder, unique_filename)
                        
                        # Sauvegarder le fichier
                        file.save(file_path)
                        
                        # Créer l'enregistrement en base
                        attachment = IncidentAttachment(
                            incident_id=nouvel_incident.id,
                            filename=unique_filename,
                            original_filename=original_filename,
                            file_path=file_path,
                            file_size=os.path.getsize(file_path),
                            mime_type=mimetypes.guess_type(original_filename)[0],
                            upload_date=datetime.now()
                        )
                        
                        db.session.add(attachment)
                        attachments_saved += 1
                        
                    except Exception as e:
                        print(f"Erreur lors de la sauvegarde du fichier {file.filename}: {e}")
                        # Continuer avec les autres fichiers
        
        # Mettre à jour l'incident avec les informations sur les fichiers
        nouvel_incident.has_attachments = attachments_saved > 0
        nouvel_incident.attachments_count = attachments_saved
        
        # Valider toutes les modifications
        db.session.commit()
        
        # Message de succès
        if attachments_saved > 0:
            flash(f'Incident "{titre}" ajouté avec succès avec {attachments_saved} fichier(s) joint(s)!', 'success')
        else:
            flash(f'Incident "{titre}" ajouté avec succès dans Azure SQL Database!', 'success')
        
        # Envoyer vers Azure Queue selon les scénarios
        incident_dict = nouvel_incident.to_dict()
        
        # Scénario 1: Notifications pour incidents critiques
        if severite == 'Critique':
            print(f"🚨 Incident critique créé: {titre} - ID: {nouvel_incident.id}")
            send_to_azure_queue(incident_dict, "critical_incident_notification")
        
        # Scénario 2: Rapports pour tous les incidents (traitement en arrière-plan)
        send_to_azure_queue(incident_dict, "incident_analytics")
        
        # Scénario 4: Traitement des fichiers joints
        if attachments_saved > 0:
            file_processing_data = {
                "incident_id": nouvel_incident.id,
                "files_count": attachments_saved,
                "attachments": [att.to_dict() for att in nouvel_incident.attachments]
            }
            send_to_azure_queue(file_processing_data, "file_processing")
        
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

@app.route('/download/<int:attachment_id>')
def download_attachment(attachment_id):
    """Télécharger un fichier joint"""
    try:
        attachment = IncidentAttachment.query.get_or_404(attachment_id)
        
        # Vérifier que le fichier existe
        if os.path.exists(attachment.file_path):
            directory = os.path.dirname(attachment.file_path)
            filename = os.path.basename(attachment.file_path)
            return send_from_directory(directory, filename, 
                                     as_attachment=True, 
                                     download_name=attachment.original_filename)
        else:
            flash('Fichier non trouvé', 'error')
            return redirect(url_for('detail_incident', incident_id=attachment.incident_id))
            
    except Exception as e:
        flash(f'Erreur lors du téléchargement: {str(e)}', 'error')
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