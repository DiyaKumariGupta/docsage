import boto3
import os
from dotenv import load_dotenv

load_dotenv()
s3 = boto3.client("s3")

def upload_to_s3(local_file, bucket_name):
    file_name = os.path.basename(local_file)
    s3.upload_file(local_file, bucket_name, file_name)
    print(f"✅ Uploaded {file_name} to {bucket_name}")
