# services/firebase_service.py
import firebase_admin
from firebase_admin import credentials, firestore
import os

db = None

def init_firebase():
    global db
    if not firebase_admin._apps:
        cred_path = os.path.join("firebase_config.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        
init_firebase()
db = firestore.client()

def adicionar_transacao(dados):
    init_firebase()
    return db.collection('transacoes').add(dados)

def listar_transacoes():
    init_firebase()
    docs = db.collection('transacoes').stream()
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

def atualizar_transacao(id, novos_dados):
    init_firebase()
    db.collection('transacoes').document(id).update(novos_dados)

def deletar_transacao(id):
    init_firebase()
    db.collection('transacoes').document(id).delete()

def adicionar_planejamento(dados):
    init_firebase()
    db.collection("planejamentos").add(dados)

def adicionar_documento(colecao, dados):
    init_firebase()
    db.collection(colecao).add(dados)

def obter_documentos(colecao):
    init_firebase()
    docs = db.collection(colecao).stream()
    return [doc.to_dict() for doc in docs]

def listar_documentos(colecao):
    docs = db.collection(colecao).stream()
    return [doc.to_dict() for doc in docs]