"""
Script de diagnostic Azure Queue Storage
Vérifier l'état de la queue et tester l'envoi/réception de messages
"""

import os
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
from azure.storage.queue import QueueClient, QueueServiceClient

# Charger les variables d'environnement
load_dotenv()

def check_queue_status():
    """Vérifier l'état de la queue Azure"""
    
    print("🔍 Diagnostic Azure Queue Storage")
    print("=" * 50)
    
    # Configuration
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    queue_name = os.getenv('AZURE_QUEUE_NAME', 'queue-incidents')
    
    if not connection_string:
        print("❌ AZURE_STORAGE_CONNECTION_STRING non configurée")
        return False
    
    print(f"📋 Configuration:")
    print(f"  Queue: {queue_name}")
    print(f"  Connection: {connection_string[:50]}...")
    print()
    
    try:
        # Créer le client queue
        queue_client = QueueClient.from_connection_string(
            connection_string, 
            queue_name
        )
        
        # Vérifier si la queue existe et la créer si nécessaire
        print("🔸 Test 1: Vérification/Création de la queue")
        try:
            queue_client.create_queue()
            print("  ✅ Queue créée")
        except Exception as e:
            if "QueueAlreadyExists" in str(e) or "already exists" in str(e).lower():
                print("  ℹ️  Queue existe déjà")
            else:
                print(f"  ❌ Erreur création: {e}")
                return False
        
        # Obtenir les propriétés de la queue
        print("\n🔸 Test 2: Propriétés de la queue")
        try:
            properties = queue_client.get_queue_properties()
            message_count = properties.approximate_message_count
            print(f"  📊 Nombre de messages: {message_count}")
            print(f"  📅 Dernière modification: {properties.last_modified}")
        except Exception as e:
            print(f"  ❌ Erreur propriétés: {e}")
            return False
        
        # Regarder les messages sans les supprimer
        print("\n🔸 Test 3: Messages en attente")
        try:
            messages = queue_client.peek_messages(max_messages=10)
            if messages:
                print(f"  📬 {len(messages)} message(s) trouvé(s):")
                for i, msg in enumerate(messages, 1):
                    try:
                        # Décoder le message
                        decoded_content = base64.b64decode(msg.content).decode('utf-8')
                        message_data = json.loads(decoded_content)
                        print(f"    [{i}] Type: {message_data.get('type', 'N/A')}")
                        print(f"        Timestamp: {message_data.get('timestamp', 'N/A')}")
                        if 'data' in message_data and isinstance(message_data['data'], dict):
                            print(f"        Incident: {message_data['data'].get('titre', 'N/A')}")
                    except Exception as decode_error:
                        print(f"    [{i}] Contenu brut: {msg.content[:100]}...")
            else:
                print("  📭 Aucun message en attente")
        except Exception as e:
            print(f"  ❌ Erreur lecture messages: {e}")
        
        # Test d'envoi d'un message
        print("\n🔸 Test 4: Envoi d'un message de test")
        try:
            test_message = {
                "type": "test_diagnostic",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "test_id": "diagnostic_001",
                    "message": "Test de diagnostic de la queue",
                    "source": "diagnostic_script"
                }
            }
            
            # Encoder le message
            message_json = json.dumps(test_message, ensure_ascii=False, default=str)
            message_b64 = base64.b64encode(message_json.encode('utf-8')).decode('utf-8')
            
            # Envoyer
            queue_client.send_message(message_b64)
            print("  ✅ Message de test envoyé")
            
            # Vérifier que le message est bien arrivé
            updated_properties = queue_client.get_queue_properties()
            new_count = updated_properties.approximate_message_count
            print(f"  📊 Nouveau nombre de messages: {new_count}")
            
        except Exception as e:
            print(f"  ❌ Erreur envoi: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

def test_flask_queue_integration():
    """Test de l'intégration Flask avec la queue"""
    
    print("\n🧪 Test intégration Flask")
    print("-" * 30)
    
    try:
        # Import du module Flask
        import sys
        sys.path.append('.')
        
        from app import send_to_azure_queue
        
        # Test des différents types de messages
        test_cases = [
            {
                "type": "critical_incident_notification",
                "data": {
                    "id": 999,
                    "titre": "Test Incident Critique",
                    "severite": "Critique",
                    "description": "Test notification critique"
                }
            },
            {
                "type": "incident_analytics", 
                "data": {
                    "id": 999,
                    "titre": "Test Analytics",
                    "severite": "Moyenne",
                    "created_at": datetime.now().isoformat()
                }
            },
            {
                "type": "file_processing",
                "data": {
                    "incident_id": 999,
                    "files_count": 2,
                    "attachments": [
                        {"filename": "test1.pdf", "size": 1024},
                        {"filename": "test2.jpg", "size": 2048}
                    ]
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔸 Test {i}: {test_case['type']}")
            success = send_to_azure_queue(test_case['data'], test_case['type'])
            
            if success:
                print(f"  ✅ Message {test_case['type']} envoyé")
            else:
                print(f"  ❌ Échec envoi {test_case['type']}")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Erreur import Flask: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur test Flask: {e}")
        return False

def clear_queue():
    """Vider la queue de tous ses messages"""
    
    print("\n🗑️ Nettoyage de la queue")
    print("-" * 30)
    
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    queue_name = os.getenv('AZURE_QUEUE_NAME', 'queue-incidents')
    
    try:
        queue_client = QueueClient.from_connection_string(connection_string, queue_name)
        
        # Compter les messages avant
        props_before = queue_client.get_queue_properties()
        count_before = props_before.approximate_message_count
        print(f"📊 Messages avant nettoyage: {count_before}")
        
        if count_before == 0:
            print("  ℹ️  Queue déjà vide")
            return True
        
        # Supprimer tous les messages
        deleted_count = 0
        while True:
            messages = queue_client.receive_messages(max_messages=32, visibility_timeout=10)
            if not messages:
                break
                
            for message in messages:
                queue_client.delete_message(message.id, message.pop_receipt)
                deleted_count += 1
        
        print(f"  🗑️ {deleted_count} message(s) supprimé(s)")
        
        # Vérifier que la queue est vide
        props_after = queue_client.get_queue_properties()
        count_after = props_after.approximate_message_count
        print(f"📊 Messages après nettoyage: {count_after}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}")
        return False

def monitor_queue_activity():
    """Surveiller l'activité de la queue en temps réel"""
    
    print("\n👁️ Surveillance de la queue (Ctrl+C pour arrêter)")
    print("-" * 50)
    
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    queue_name = os.getenv('AZURE_QUEUE_NAME', 'queue-incidents')
    
    try:
        queue_client = QueueClient.from_connection_string(connection_string, queue_name)
        
        import time
        last_count = 0
        
        while True:
            try:
                properties = queue_client.get_queue_properties()
                current_count = properties.approximate_message_count
                
                if current_count != last_count:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    if current_count > last_count:
                        print(f"[{timestamp}] 📈 +{current_count - last_count} nouveau(x) message(s) (Total: {current_count})")
                    elif current_count < last_count:
                        print(f"[{timestamp}] 📉 -{last_count - current_count} message(s) traité(s) (Total: {current_count})")
                    
                    last_count = current_count
                
                time.sleep(2)  # Attendre 2 secondes
                
            except KeyboardInterrupt:
                print("\n👋 Surveillance arrêtée")
                break
            except Exception as e:
                print(f"❌ Erreur surveillance: {e}")
                time.sleep(5)
        
    except Exception as e:
        print(f"❌ Erreur initialisation surveillance: {e}")

if __name__ == "__main__":
    print("🚀 Diagnostic complet Azure Queue Storage")
    print("=" * 60)
    
    # Menu interactif
    while True:
        print("\n📋 Options disponibles:")
        print("  1 - Vérifier l'état de la queue")
        print("  2 - Tester l'intégration Flask")
        print("  3 - Vider la queue")
        print("  4 - Surveiller la queue en temps réel")
        print("  0 - Quitter")
        
        choice = input("\n👆 Votre choix: ").strip()
        
        if choice == "1":
            check_queue_status()
        elif choice == "2":
            test_flask_queue_integration()
        elif choice == "3":
            confirm = input("⚠️ Êtes-vous sûr de vouloir vider la queue? (oui/non): ")
            if confirm.lower() in ['oui', 'o', 'yes', 'y']:
                clear_queue()
        elif choice == "4":
            monitor_queue_activity()
        elif choice == "0":
            print("👋 Au revoir!")
            break
        else:
            print("❌ Choix invalide")