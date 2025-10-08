import firebase_admin
from firebase_admin import credentials, storage
import os


FIREBASE_CRED_PATH = r"src\utils\mylanguageguru-b744f-firebase-adminsdk-fbsvc-c87529538e.json"


FIREBASE_BUCKET_NAME = "mylanguageguru-b744f.firebasestorage.app"  # change this

# Initialize Firebase app once
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred, {
        "storageBucket": FIREBASE_BUCKET_NAME
    })

bucket = storage.bucket()

if __name__ == "__main__":
    print("✅ Firebase connected to bucket:", bucket.name)
