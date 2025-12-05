import requests
import json
import csv
import time
import sys

BASE_URL = "http://localhost:8088/api"
API_KEY = "gorse_key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_connection():
    """Test API connection"""
    try:
        response = requests.get(f"{BASE_URL}/items?n=1", headers=headers)
        if response.status_code == 200:
            print("✓ API connection successful")
            return True
        else:
            print(f"✗ API connection failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def upload_items():
    """Upload items from items.csv"""
    print("\nUploading items...")
    
    items = []
    with open('items.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Parse the comment field
            comment = row.get('comment', '')
            
            # Parse labels
            labels = []
            if row.get('labels'):
                for label_pair in row['labels'].split('|'):
                    if ':' in label_pair:
                        labels.append(label_pair)
            
            # Parse categories
            categories = row.get('categories', '').split('|') if row.get('categories') else []
            
            item = {
                "ItemId": row['item_id'],
                "Timestamp": row.get('timestamp', ''),
                "Labels": labels,
                "Categories": categories,
                "Comment": comment
            }
            items.append(item)
    
    print(f"Found {len(items)} items to upload")
    
    # Upload items in batches
    batch_size = 10
    success_count = 0
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        try:
            response = requests.put(f"{BASE_URL}/items", json=batch, headers=headers)
            if response.status_code == 200:
                success_count += len(batch)
                print(f"✓ Batch {i//batch_size + 1}: Uploaded {len(batch)} items")
            else:
                print(f"✗ Batch {i//batch_size + 1}: Failed with status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Batch {i//batch_size + 1}: Error: {e}")
        time.sleep(0.1)
    
    print(f"\nTotal items uploaded: {success_count}/{len(items)}")
    return success_count

def upload_feedback():
    """Upload feedback from feedback.csv"""
    print("\nUploading feedback...")
    
    feedback_list = []
    with open('feedback.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Extract weight from comment if present
            comment = row.get('comment', '')
            
            feedback = {
                "FeedbackType": row['feedback_type'],
                "UserId": row['user_id'],
                "ItemId": row['item_id'],
                "Timestamp": row.get('timestamp', ''),
                "Comment": comment
            }
            feedback_list.append(feedback)
    
    print(f"Found {len(feedback_list)} feedback entries to upload")
    
    # Upload feedback in batches
    batch_size = 20
    success_count = 0
    
    for i in range(0, len(feedback_list), batch_size):
        batch = feedback_list[i:i+batch_size]
        try:
            response = requests.post(f"{BASE_URL}/feedback", json=batch, headers=headers)
            if response.status_code == 200:
                success_count += len(batch)
                print(f"✓ Batch {i//batch_size + 1}: Uploaded {len(batch)} feedback entries")
            else:
                print(f"✗ Batch {i//batch_size + 1}: Failed with status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Batch {i//batch_size + 1}: Error: {e}")
        time.sleep(0.1)
    
    print(f"\nTotal feedback entries uploaded: {success_count}/{len(feedback_list)}")
    return success_count

def trigger_training():
    """Trigger model training"""
    print("\nTriggering model training...")
    try:
        response = requests.post(f"{BASE_URL}/train", headers=headers)
        if response.status_code == 200:
            print("✓ Training triggered successfully")
        else:
            print(f"✗ Training trigger failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Error triggering training: {e}")

if __name__ == "__main__":
    print("=== Gorse Data Upload Script ===")
    
    # Check if CSV files exist
    import os
    if not os.path.exists('items.csv'):
        print("✗ Error: items.csv not found in current directory")
        sys.exit(1)
    
    if not os.path.exists('feedback.csv'):
        print("✗ Error: feedback.csv not found in current directory")
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        print("\nPlease ensure Gorse is running and accessible at http://localhost:8088")
        sys.exit(1)
    
    # Upload data
    items_uploaded = upload_items()
    feedback_uploaded = upload_feedback()
    
    # Trigger training
    if items_uploaded > 0 and feedback_uploaded > 0:
        trigger_training()
    
    print("\n=== Upload Complete ===")
    print("\nNext steps:")
    print("1. Wait a few minutes for training to complete")
    print("2. Test recommendations with:")
    print('   curl -H "X-API-Key: gorse_key" "http://localhost:8088/api/recommend/9b6d5856-b182-4c98-97ee-982ebc116943?n=5"')
    print('   curl -H "X-API-Key: gorse_key" "http://localhost:8088/api/recommend/68c3b151-6662-4096-a197-233ac78d7ad5?n=5"')
    print("\n3. Check dashboard at: http://localhost:8088")
