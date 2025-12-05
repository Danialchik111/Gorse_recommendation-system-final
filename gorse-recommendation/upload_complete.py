import requests
import json
import csv
import time

BASE_URL = "http://localhost:8088/api"
API_KEY = "gorse_key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def upload_all_items():
    """Upload all items from items.csv"""
    print("Uploading all items from items.csv...")
    
    items = []
    
    # First, try to read from items.csv file
    try:
        with open('items.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
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
                    "Comment": row.get('comment', '')
                }
                items.append(item)
        
        print(f"Found {len(items)} items in CSV")
    except FileNotFoundError:
        print("items.csv not found, using sample data")
        # Fall back to sample data
        items = [
            {
                "ItemId": "HD37654191",
                "Timestamp": "1758007507",
                "Labels": ["estate:黃埔花園", "region:黃埔"],
                "Categories": ["rental"],
                "Comment": "{\"rent_price\": 25000.0}"
            },
            {
                "ItemId": "HD37654247",
                "Timestamp": "1758016208",
                "Labels": ["estate:黃埔花園", "region:黃埔"],
                "Categories": ["sale"],
                "Comment": "{\"sale_price\": 8100000.0}"
            },
            {
                "ItemId": "HD37654143",
                "Timestamp": "1758033196",
                "Labels": ["estate:斌善軒", "region:錦田"],
                "Categories": ["rental"],
                "Comment": "{\"rent_price\": 13500.0}"
            },
            {
                "ItemId": "HD37654213",
                "Timestamp": "1758075661",
                "Labels": ["estate:黃埔花園", "region:黃埔"],
                "Categories": ["sale"],
                "Comment": "{\"sale_price\": 6080000.0}"
            },
            {
                "ItemId": "HD37654250",
                "Timestamp": "1758075751",
                "Labels": ["estate:錦豐花園", "region:錦田"],
                "Categories": ["rental", "sale"],
                "Comment": "{\"rent_price\": 15000.0, \"sale_price\": 5600000.0}"
            }
        ]
    
    # Upload in batches
    batch_size = 10
    total_uploaded = 0
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        try:
            response = requests.post(f"{BASE_URL}/items", json=batch, headers=headers)
            if response.status_code == 200:
                result = response.json()
                affected = result.get('RowAffected', len(batch))
                total_uploaded += affected
                print(f"✓ Batch {i//batch_size + 1}: Uploaded {affected} items")
            else:
                print(f"✗ Batch {i//batch_size + 1}: Failed with status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Batch {i//batch_size + 1}: Error: {e}")
        
        # Small delay to avoid overwhelming
        time.sleep(0.1)
    
    print(f"\nTotal items uploaded: {total_uploaded}/{len(items)}")
    return total_uploaded

def upload_all_feedback():
    """Upload all feedback from feedback.csv"""
    print("\nUploading feedback from feedback.csv...")
    
    feedback_list = []
    
    try:
        with open('feedback.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                feedback = {
                    "FeedbackType": row['feedback_type'],
                    "UserId": row['user_id'],
                    "ItemId": row['item_id'],
                    "Timestamp": row.get('timestamp', ''),
                    "Comment": row.get('comment', '')
                }
                feedback_list.append(feedback)
        
        print(f"Found {len(feedback_list)} feedback entries in CSV")
    except FileNotFoundError:
        print("feedback.csv not found, using sample data")
        # Fall back to sample feedback
        feedback_list = [
            {
                "FeedbackType": "view_listing",
                "UserId": "9b6d5856-b182-4c98-97ee-982ebc116943",
                "ItemId": "HD37654191",
                "Timestamp": "1758007507",
                "Comment": "weight:1.0"
            },
            {
                "FeedbackType": "view_listing",
                "UserId": "9b6d5856-b182-4c98-97ee-982ebc116943",
                "ItemId": "HD37654191",
                "Timestamp": "1758007530",
                "Comment": "weight:1.0"
            },
            {
                "FeedbackType": "view_listing",
                "UserId": "9b6d5856-b182-4c98-97ee-982ebc116943",
                "ItemId": "HD37654247",
                "Timestamp": "1758016208",
                "Comment": "weight:1.0"
            },
            {
                "FeedbackType": "view_listing",
                "UserId": "cb987911-b3a0-47fd-a25c-fdf8f3c18bba",
                "ItemId": "HD37654143",
                "Timestamp": "1758033196",
                "Comment": "weight:1.0"
            },
            {
                "FeedbackType": "contact_agent",
                "UserId": "2db80906-9b4b-4649-b648-b58b46c3c048",
                "ItemId": "HD37655491",
                "Timestamp": "1759818321",
                "Comment": "weight:3.0"
            }
        ]
    
    # Upload in batches
    batch_size = 20
    total_uploaded = 0
    
    for i in range(0, len(feedback_list), batch_size):
        batch = feedback_list[i:i+batch_size]
        try:
            response = requests.post(f"{BASE_URL}/feedback", json=batch, headers=headers)
            if response.status_code == 200:
                result = response.json()
                affected = result.get('RowAffected', len(batch))
                total_uploaded += affected
                print(f"✓ Batch {i//batch_size + 1}: Uploaded {affected} feedback entries")
            else:
                print(f"✗ Batch {i//batch_size + 1}: Failed with status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Batch {i//batch_size + 1}: Error: {e}")
        
        time.sleep(0.1)
    
    print(f"\nTotal feedback entries uploaded: {total_uploaded}/{len(feedback_list)}")
    return total_uploaded

def trigger_training_and_wait():
    """Trigger training and wait for completion"""
    print("\nTriggering model training...")
    
    try:
        response = requests.post(f"{BASE_URL}/train", headers=headers)
        if response.status_code == 200:
            print("✓ Training triggered successfully")
        else:
            print(f"✗ Training trigger failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error triggering training: {e}")
        return False
    
    # Wait for training to complete
    print("\nWaiting 30 seconds for training to complete...")
    for i in range(30):
        print(f".", end="", flush=True)
        time.sleep(1)
    print()
    
    return True

def test_recommendations():
    """Test recommendations for sample users"""
    print("\n=== Testing Recommendations ===")
    
    test_users = [
        "9b6d5856-b182-4c98-97ee-982ebc116943",
        "cb987911-b3a0-47fd-a25c-fdf8f3c18bba",
        "68c3b151-6662-4096-a197-233ac78d7ad5",
        "2db80906-9b4b-4649-b648-b58b46c3c048"
    ]
    
    for user_id in test_users:
        print(f"\nRecommendations for user {user_id}:")
        try:
            response = requests.get(
                f"{BASE_URL}/recommend/{user_id}?n=5",
                headers=headers
            )
            if response.status_code == 200:
                recommendations = response.json()
                if recommendations:
                    print(f"✓ Found {len(recommendations)} recommendations")
                    for i, rec in enumerate(recommendations[:3]):  # Show first 3
                        print(f"  {i+1}. Item ID: {rec.get('Id', 'N/A')}, Score: {rec.get('Score', 'N/A')}")
                else:
                    print("✗ No recommendations available yet")
            else:
                print(f"✗ API error: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    print("=== Gorse Real Estate Recommendation System ===")
    print("Starting data upload and setup...")
    
    # Upload data
    items_count = upload_all_items()
    feedback_count = upload_all_feedback()
    
    if items_count > 0 and feedback_count > 0:
        # Trigger training
        if trigger_training_and_wait():
            # Test recommendations
            test_recommendations()
    else:
        print("\nInsufficient data uploaded. Need both items and feedback.")
    
    print("\n=== Setup Complete ===")
    print("\nNext steps:")
    print("1. Check dashboard: http://localhost:8088")
    print("2. Monitor training progress in dashboard")
    print("3. Use these API endpoints:")
    print("   - List items: GET /api/items?n=10")
    print("   - Get recommendations: GET /api/recommend/{user_id}?n=10")
    print("   - Insert feedback: POST /api/feedback")
    print("   - Insert items: POST /api/items")
    print("\nExample API calls:")
    print('   curl -H "X-API-Key: gorse_key" "http://localhost:8088/api/items?n=5"')
    print('   curl -H "X-API-Key: gorse_key" "http://localhost:8088/api/recommend/9b6d5856-b182-4c98-97ee-982ebc116943?n=5"')
