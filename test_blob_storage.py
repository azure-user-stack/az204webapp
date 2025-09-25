"""
Script de test pour Azure Blob Storage
Test d'upload, de téléchargement et de suppression de fichiers
"""

import os
import io
from dotenv import load_dotenv
from azure_blob_manager import AzureBlobManager

# Charger les variables d'environnement
load_dotenv()

def test_azure_blob_storage():
    """Test complet d'Azure Blob Storage"""
    
    print("🧪 Test Azure Blob Storage Manager")
    print("=" * 50)
    
    # Configuration
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME', 'incident-attachments')
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING non configurée")
        return False
    
    try:
        # Initialiser le gestionnaire
        print("📦 Initialisation du gestionnaire Blob...")
        blob_manager = AzureBlobManager(connection_string, container_name)
        
        # Test 1: Créer un fichier test
        print("\n🔸 Test 1: Upload d'un fichier test")
        test_content = "Ceci est un fichier de test pour Azure Blob Storage\nCréé pour tester l'intégration Flask"
        test_file = io.BytesIO(test_content.encode('utf-8'))
        test_file.filename = "test_document.txt"
        
        # Simuler un FileStorage
        class MockFileStorage:
            def __init__(self, content, filename):
                self.content = content
                self.filename = filename
                self._position = 0
            
            def read(self):
                self.content.seek(0)
                return self.content.read()
            
            def seek(self, pos, whence=0):
                if whence == 0:  # SEEK_SET
                    self._position = pos
                elif whence == 2:  # SEEK_END
                    self._position = len(self.content.getvalue())
                self.content.seek(self._position)
            
            def tell(self):
                return self._position
        
        mock_file = MockFileStorage(test_file, "test_document.txt")
        
        # Upload du fichier
        allowed_extensions = ['txt', 'pdf', 'jpg', 'png']
        upload_result = blob_manager.upload_file(
            file=mock_file,
            incident_id=999,  # ID de test
            allowed_extensions=allowed_extensions,
            max_file_size_mb=10
        )
        
        if upload_result['success']:
            print(f"  ✅ Upload réussi: {upload_result['blob_name']}")
            blob_name = upload_result['blob_name']
        else:
            print(f"  ❌ Échec upload: {upload_result.get('error')}")
            return False
        
        # Test 2: Générer URL de téléchargement
        print("\n🔸 Test 2: Génération URL de téléchargement")
        download_url = blob_manager.generate_download_url(blob_name, expiry_hours=1)
        
        if download_url:
            print(f"  ✅ URL générée (valide 1h):")
            print(f"  🔗 {download_url[:80]}...")
        else:
            print("  ❌ Échec génération URL")
        
        # Test 3: Récupérer les informations du fichier
        print("\n🔸 Test 3: Informations du fichier")
        file_info = blob_manager.get_file_info(blob_name)
        
        if file_info:
            print(f"  ✅ Fichier trouvé:")
            print(f"    📁 Nom: {file_info['blob_name']}")
            print(f"    📏 Taille: {file_info['size']} bytes")
            print(f"    📅 Modifié: {file_info['last_modified']}")
            print(f"    🏷️ Type: {file_info.get('content_type', 'N/A')}")
        else:
            print("  ❌ Fichier non trouvé")
        
        # Test 4: Lister les fichiers de l'incident
        print("\n🔸 Test 4: Liste des fichiers de l'incident 999")
        incident_files = blob_manager.list_incident_files(999)
        
        print(f"  📋 {len(incident_files)} fichier(s) trouvé(s):")
        for file_info in incident_files:
            print(f"    📄 {file_info['blob_name']} ({file_info['size']} bytes)")
        
        # Test 5: Statistiques du container
        print("\n🔸 Test 5: Statistiques du container")
        stats = blob_manager.get_container_stats()
        
        if 'error' not in stats:
            print(f"  📊 Container: {stats['container_name']}")
            print(f"  📁 Total fichiers: {stats['total_files']}")
            print(f"  💾 Taille totale: {stats['total_size_mb']} MB")
            print(f"  🏷️ Types de fichiers: {stats['file_types']}")
        else:
            print(f"  ❌ Erreur stats: {stats['error']}")
        
        # Test 6: Suppression du fichier test
        print("\n🔸 Test 6: Suppression du fichier test")
        delete_success = blob_manager.delete_file(blob_name)
        
        if delete_success:
            print("  ✅ Fichier supprimé avec succès")
        else:
            print("  ❌ Échec suppression")
        
        print("\n" + "=" * 50)
        print("🎉 Tests Azure Blob Storage terminés avec succès!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur durant les tests: {e}")
        return False

def test_file_validations():
    """Test des validations de fichiers"""
    
    print("\n🧪 Test des validations de fichiers")
    print("-" * 30)
    
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        print("❌ Connection string manquante")
        return False
    
    blob_manager = AzureBlobManager(connection_string)
    allowed_extensions = ['txt', 'pdf', 'jpg', 'png']
    
    # Test des extensions
    test_files = [
        ("document.txt", True),
        ("image.jpg", True),
        ("archive.zip", False),
        ("script.exe", False),
        ("data.json", False),
        ("photo.PNG", True),  # Test insensible à la casse
    ]
    
    print("🔸 Test validation extensions:")
    for filename, should_be_valid in test_files:
        is_valid = blob_manager.is_file_allowed(filename, allowed_extensions)
        status = "✅" if is_valid == should_be_valid else "❌"
        print(f"  {status} {filename}: {is_valid} (attendu: {should_be_valid})")
    
    print("\n🔸 Test génération noms uniques:")
    for i in range(3):
        unique_name = blob_manager.generate_unique_filename("test.txt", 123)
        print(f"  📝 {unique_name}")

if __name__ == "__main__":
    print("🚀 Test complet Azure Blob Storage Manager")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    if not os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
        print("❌ Variables d'environnement manquantes")
        print("Vérifiez que AZURE_STORAGE_CONNECTION_STRING est configurée dans .env")
        exit(1)
    
    # Tests principaux
    success = test_azure_blob_storage()
    
    if success:
        # Tests des validations
        test_file_validations()
        print("\n🎉 Tous les tests sont passés!")
    else:
        print("\n💥 Certains tests ont échoué")
        exit(1)