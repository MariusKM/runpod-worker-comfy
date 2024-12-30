import boto3
import os

# Initialize S3 client
s3 = boto3.client('s3')

# Bucket and prefix configuration
bucket_name = 'jasper-250-runpod-staging-external-service-bucket'
prefix = '12-24/PortlandClassicNew/'

def clean_key(key):
    # Keep the directory structure but clean the filename
    path_parts = key.split('/')
    # Clean only the filename (last part)
    if path_parts:
        path_parts[-1] = path_parts[-1].replace('\n', '').replace('\r', '')
    # Rejoin the path
    return '/'.join(path_parts)

def fix_filenames():
    # List all objects in the bucket under the prefix
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            old_key = obj['Key']
            if '\n' in old_key or '\r' in old_key:
                new_key = clean_key(old_key)
                print(f"Renaming: {old_key} -> {new_key}")
                
                try:
                    # Copy object to new key
                    s3.copy_object(
                        Bucket=bucket_name,
                        CopySource={'Bucket': bucket_name, 'Key': old_key},
                        Key=new_key
                    )
                    print(f"Successfully created {new_key}")
                except Exception as e:
                    print(f"Error copying {old_key}: {str(e)}")

# Add dry run mode for safety
DRY_RUN = False  # Set to False when ready to make actual changes

if __name__ == "__main__":
    if DRY_RUN:
        print("Running in DRY RUN mode - no changes will be made")
    fix_filenames()