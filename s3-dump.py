import boto3
import os
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

MAX_WORKERS = 8  # Adjust based on your system

# Unauthenticated S3 client
s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

def safe_filename(s3_key, download_dir='.'):
    """Ensure that S3 key is safely saved locally in the specified directory."""
    return os.path.join(download_dir, s3_key)

def download_file(bucket_name, key, download_dir='.'):
    local_path = safe_filename(key, download_dir)
    local_dir = os.path.dirname(local_path)
    os.makedirs(local_dir, exist_ok=True)
    try:
        s3.download_file(bucket_name, key, local_path)
        return {"status": "success", "key": key, "message": f"[✓] Downloaded: {key}"}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            return {"status": "access_denied", "key": key, "message": f"[🔒] Access Denied: {key}"}
        elif error_code == 'NoSuchKey':
            return {"status": "not_found", "key": key, "message": f"[❓] Not Found: {key}"}
        else:
            return {"status": "error", "key": key, "message": f"[✗] AWS Error ({error_code}): {key} - {e}"}
    except Exception as e:
        return {"status": "error", "key": key, "message": f"[✗] Failed: {key} - {e}"}

def list_all_keys(bucket_name, prefix=''):
    keys = []
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            contents = page.get('Contents', [])
            for obj in contents:
                keys.append(obj['Key'])
        return keys, None
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            return [], f"Access denied to bucket '{bucket_name}'. The bucket might be private or require authentication."
        elif error_code == 'NoSuchBucket':
            return [], f"Bucket '{bucket_name}' does not exist."
        else:
            return [], f"AWS Error ({error_code}): {e}"
    except Exception as e:
        return [], f"Unexpected error: {e}"

def download_bucket(bucket_name, prefix='', download_dir='.'):
    print(f"🔍 Enumerating files in bucket: {bucket_name} (prefix: '{prefix}')")
    keys, list_error = list_all_keys(bucket_name, prefix)
    
    if list_error:
        print(f"❌ Cannot access bucket: {list_error}")
        return
    
    if not keys:
        print("⚠️  No files found in the specified bucket/prefix.")
        return
    
    # Ensure download directory exists
    os.makedirs(download_dir, exist_ok=True)
    print(f"📁 Download directory: {os.path.abspath(download_dir)}")
    print(f"📦 Found {len(keys)} files. Starting download...")
    
    # Download files with progress bar
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(tqdm(
            executor.map(lambda key: download_file(bucket_name, key, download_dir), keys), 
            total=len(keys),
            desc="Downloading"
        ))
    
    # Categorize results
    successful = [r for r in results if r["status"] == "success"]
    access_denied = [r for r in results if r["status"] == "access_denied"]
    errors = [r for r in results if r["status"] in ["error", "not_found"]]
    
    # Print summary
    print(f"\n--- Download Summary ---")
    print(f"✅ Successfully downloaded: {len(successful)} files")
    if access_denied:
        print(f"🔒 Access denied: {len(access_denied)} files")
    if errors:
        print(f"❌ Other errors: {len(errors)} files")
    
    # Show details for access denied and errors
    if access_denied:
        print(f"\n🔒 Files with access denied:")
        for result in access_denied[:10]:  # Show first 10
            print(f"   - {result['key']}")
        if len(access_denied) > 10:
            print(f"   ... and {len(access_denied) - 10} more")
        print("   💡 These files might require authentication or special permissions.")
    
    if errors:
        print(f"\n❌ Other errors:")
        for result in errors[:5]:  # Show first 5 errors
            print(f"   - {result['message']}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more errors")
    
    # Final status
    total_files = len(results)
    success_rate = (len(successful) / total_files) * 100 if total_files > 0 else 0
    print(f"\n📊 Overall success rate: {success_rate:.1f}% ({len(successful)}/{total_files})")
    
    if success_rate < 100 and success_rate > 0:
        print("💡 Consider checking bucket permissions or using authenticated access for restricted files.")

def validate_bucket_access(bucket_name):
    """Test basic access to the bucket before proceeding."""
    try:
        # Try to list just one object to test access
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        return True, None
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            return False, f"🔒 Access denied to bucket '{bucket_name}'. This bucket appears to be private."
        elif error_code == 'NoSuchBucket':
            return False, f"❌ Bucket '{bucket_name}' does not exist."
        else:
            return False, f"❌ AWS Error ({error_code}): {e}"
    except Exception as e:
        return False, f"❌ Unexpected error: {e}"
    """Get and validate the download directory from user input."""
    while True:
        download_dir = input("Enter the download directory path (or leave blank for current directory): ").strip()
        
        if not download_dir:
            return '.'
        
        # Expand user path (handles ~ for home directory)
        download_dir = os.path.expanduser(download_dir)
        
        # Check if it's an absolute path or make it relative to current directory
        if not os.path.isabs(download_dir):
            download_dir = os.path.abspath(download_dir)
        
        try:
            # Test if we can create the directory
            os.makedirs(download_dir, exist_ok=True)
            print(f"✓ Download directory set to: {download_dir}")
            return download_dir
        except PermissionError:
            print(f"❌ Permission denied: Cannot create directory '{download_dir}'")
            print("Please enter a different path or ensure you have write permissions.")
        except OSError as e:
            print(f"❌ Invalid path: {e}")
            print("Please enter a valid directory path.")

# Main execution
if __name__ == "__main__":
    print(r"""
  ____ _____ ____                            _            
 / ___|___ /|  _ \ _   _ _ __ ___  _ __  ___| |_ ___ _ __ 
 \___ \ |_ \| | | | | | | '_ ` _ \| '_ \/ __| __/ _ \ '__|
  ___) |__) | |_| | |_| | | | | | | |_) \__ \ ||  __/ |   
 |____/____/|____/ \__,_|_| |_| |_| .__/|___/\__\___|_|   
                                 |_|                     
""")
    
    bucket_name = input("Enter the public S3 bucket name: ").strip()
    
    # Test bucket access first
    print("🔍 Testing bucket access...")
    access_ok, error_msg = validate_bucket_access(bucket_name)
    
    if not access_ok:
        print(error_msg)
        response = input("\n❓ Do you want to continue anyway? Some files might still be accessible (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("👋 Exiting...")
            exit(0)
        print("⚠️  Continuing with limited access - some files may fail to download.\n")
    else:
        print("✅ Bucket access confirmed.\n")
    
    prefix = input("Enter the prefix (or leave blank for full bucket): ").strip()
    download_dir = get_download_directory()
    
    print(f"\n🚀 Starting download from bucket '{bucket_name}' to '{download_dir}'")
    download_bucket(bucket_name, prefix, download_dir)
