
import firebase_admin
from firebase_admin import credentials, firestore
import os


cred_path = os.path.join(os.path.dirname(__file__), '../firebase_config.json')

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()


def salvar_dado(colecao, dados):
    return db.collection(colecao).add(dados)

def obter_dados(colecao):
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection(colecao).stream()]
