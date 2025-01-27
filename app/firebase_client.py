import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("config/secrets.json")
firebase_admin.initialize_app(cred, {"storageBucket": "your_bucket_name"})

def upload_to_firebase(local_path, cloud_path):
    bucket = storage.bucket()
    blob = bucket.blob(cloud_path)
    blob.upload_from_filename(local_path)
    print(f"文件已上传到Firebase: {cloud_path}")
    return blob.public_url
