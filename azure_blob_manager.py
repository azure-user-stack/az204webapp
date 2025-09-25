"""
Azure Blob Storage Manager
Module pour gérer l'upload et le téléchargement de fichiers via Azure Blob Storage
"""

import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError


class AzureBlobManager:
    """Gestionnaire pour Azure Blob Storage"""
    
    def __init__(self, connection_string: str, container_name: str = "incident-attachments"):
        """
        Initialiser le gestionnaire Blob
        
        Args:
            connection_string: Connection string Azure Storage
            container_name: Nom du container pour stocker les fichiers
        """
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
        
        # Créer le container s'il n'existe pas
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Créer le container s'il n'existe pas"""
        try:
            self.container_client.create_container()  # Container privé par défaut
            print(f"✅ Container '{self.container_name}' créé")
        except ResourceExistsError:
            print(f"ℹ️  Container '{self.container_name}' existe déjà")
        except Exception as e:
            print(f"❌ Erreur création container: {e}")
    
    def is_file_allowed(self, filename: str, allowed_extensions: List[str]) -> bool:
        """
        Vérifier si le type de fichier est autorisé
        
        Args:
            filename: Nom du fichier
            allowed_extensions: Liste des extensions autorisées
            
        Returns:
            True si le fichier est autorisé
        """
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in [ext.lower() for ext in allowed_extensions]
    
    def generate_unique_filename(self, original_filename: str, incident_id: int) -> str:
        """
        Générer un nom de fichier unique
        
        Args:
            original_filename: Nom original du fichier
            incident_id: ID de l'incident
            
        Returns:
            Nom de fichier unique
        """
        # Sécuriser le nom de fichier
        safe_filename = secure_filename(original_filename)
        
        # Extraire l'extension
        name, ext = os.path.splitext(safe_filename)
        
        # Générer un nom unique avec timestamp et UUID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Format: incident_ID_timestamp_uniqueID_originalname.ext
        unique_filename = f"incident_{incident_id}_{timestamp}_{unique_id}_{name}{ext}"
        
        return unique_filename
    
    def upload_file(
        self, 
        file: FileStorage, 
        incident_id: int, 
        allowed_extensions: List[str],
        max_file_size_mb: int = 10
    ) -> Dict[str, any]:
        """
        Uploader un fichier vers Azure Blob Storage
        
        Args:
            file: Fichier à uploader
            incident_id: ID de l'incident
            allowed_extensions: Extensions autorisées
            max_file_size_mb: Taille max en MB
            
        Returns:
            Dict contenant les informations du fichier uploadé
        """
        try:
            # Vérifications de base
            if not file or not file.filename:
                raise ValueError("Aucun fichier sélectionné")
            
            if not self.is_file_allowed(file.filename, allowed_extensions):
                raise ValueError(f"Type de fichier non autorisé. Extensions autorisées: {', '.join(allowed_extensions)}")
            
            # Vérifier la taille du fichier
            file.seek(0, os.SEEK_END)  # Aller à la fin du fichier
            file_size = file.tell()
            file.seek(0)  # Revenir au début
            
            max_size_bytes = max_file_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                raise ValueError(f"Fichier trop volumineux. Taille max: {max_file_size_mb}MB")
            
            # Générer nom unique
            unique_filename = self.generate_unique_filename(file.filename, incident_id)
            
            # Détecter le type MIME
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # Uploader vers Blob Storage
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=unique_filename
            )
            
            # Métadonnées pour le blob
            metadata = {
                "incident_id": str(incident_id),
                "original_filename": file.filename,
                "upload_date": datetime.now().isoformat(),
                "file_size": str(file_size),
                "mime_type": mime_type
            }
            
            # Upload avec métadonnées
            blob_client.upload_blob(
                file.read(),
                overwrite=True,
                metadata=metadata,
                content_settings=ContentSettings(content_type=mime_type)
            )
            
            print(f"✅ Fichier uploadé: {unique_filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "blob_name": unique_filename,
                "original_filename": file.filename,
                "file_size": file_size,
                "mime_type": mime_type,
                "url": blob_client.url,
                "container": self.container_name
            }
            
        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_download_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """
        Générer une URL de téléchargement sécurisée avec SAS token
        
        Args:
            blob_name: Nom du blob
            expiry_hours: Durée de validité en heures
            
        Returns:
            URL sécurisée pour télécharger le fichier
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Générer SAS token
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self._get_account_key(),
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            return f"{blob_client.url}?{sas_token}"
            
        except Exception as e:
            print(f"❌ Erreur génération URL: {e}")
            return ""
    
    def _get_account_key(self) -> str:
        """Extraire la clé de compte depuis la connection string"""
        try:
            # Parser la connection string pour extraire AccountKey
            parts = self.connection_string.split(';')
            for part in parts:
                if part.startswith('AccountKey='):
                    return part.split('=', 1)[1]
            raise ValueError("AccountKey non trouvée dans connection string")
        except Exception as e:
            print(f"❌ Erreur extraction clé: {e}")
            return ""
    
    def delete_file(self, blob_name: str) -> bool:
        """
        Supprimer un fichier du Blob Storage
        
        Args:
            blob_name: Nom du blob à supprimer
            
        Returns:
            True si suppression réussie
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            print(f"✅ Fichier supprimé: {blob_name}")
            return True
            
        except ResourceNotFoundError:
            print(f"⚠️ Fichier non trouvé: {blob_name}")
            return False
        except Exception as e:
            print(f"❌ Erreur suppression: {e}")
            return False
    
    def get_file_info(self, blob_name: str) -> Optional[Dict[str, any]]:
        """
        Récupérer les informations d'un fichier
        
        Args:
            blob_name: Nom du blob
            
        Returns:
            Dict avec les informations du fichier ou None
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            return {
                "blob_name": blob_name,
                "size": properties.size,
                "last_modified": properties.last_modified,
                "content_type": properties.content_settings.content_type,
                "metadata": properties.metadata,
                "url": blob_client.url
            }
            
        except ResourceNotFoundError:
            print(f"⚠️ Fichier non trouvé: {blob_name}")
            return None
        except Exception as e:
            print(f"❌ Erreur récupération info: {e}")
            return None
    
    def list_incident_files(self, incident_id: int) -> List[Dict[str, any]]:
        """
        Lister tous les fichiers d'un incident
        
        Args:
            incident_id: ID de l'incident
            
        Returns:
            Liste des fichiers avec leurs informations
        """
        try:
            files = []
            prefix = f"incident_{incident_id}_"
            
            for blob in self.container_client.list_blobs(name_starts_with=prefix):
                file_info = {
                    "blob_name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None
                }
                
                # Ajouter métadonnées si disponibles
                if hasattr(blob, 'metadata') and blob.metadata:
                    file_info.update(blob.metadata)
                
                files.append(file_info)
            
            return files
            
        except Exception as e:
            print(f"❌ Erreur listage fichiers: {e}")
            return []
    
    def get_container_stats(self) -> Dict[str, any]:
        """
        Récupérer les statistiques du container
        
        Returns:
            Dict avec les statistiques
        """
        try:
            blobs = list(self.container_client.list_blobs())
            
            total_files = len(blobs)
            total_size = sum(blob.size for blob in blobs)
            
            # Grouper par type de fichier
            file_types = {}
            for blob in blobs:
                content_type = blob.content_settings.content_type if blob.content_settings else "unknown"
                file_types[content_type] = file_types.get(content_type, 0) + 1
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "container_name": self.container_name
            }
            
        except Exception as e:
            print(f"❌ Erreur stats container: {e}")
            return {
                "error": str(e)
            }