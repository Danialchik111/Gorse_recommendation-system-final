# System overview

Gorse is running in Docker with:
- API: http://localhost:8088
- Dashboard: http://localhost:8088 (web interface)
- MySQL: localhost:3306
- Redis: localhost:6379

## API Key
Use API key: `gorse_key` in header `X-API-Key`

### 1. Get Recommendations for User

### Get personalized recommendations
curl -H "X-API-Key: gorse_key" \\
  "http://localhost:8088/api/recommend/{USER_ID}?n=10"

### Example for specific user
curl -H "X-API-Key: gorse_key" \\
  "http://localhost:8088/api/recommend/9b6d5856-b182-4c98-97ee-982ebc116943?n=5"

### Get details of a specific property
curl -H "X-API-Key: gorse_key" \\
  "http://localhost:8088/api/item/{ITEM_ID}"

### Example
curl -H "X-API-Key: gorse_key" \\
  "http://localhost:8088/api/item/HD37664580"

### When user views a listing
curl -X POST -H "X-API-Key: gorse_key" \\
  -H "Content-Type: application/json" \\
  -d '[{
    "FeedbackType": "view_listing",
    "UserId": "USER_ID",
    "ItemId": "ITEM_ID",
    "Timestamp": "UNIX_TIMESTAMP",
    "Comment": "weight:1.0"
  }]' \\
  http://localhost:8088/api/feedback

### When user contacts agent (higher weight)
curl -X POST -H "X-API-Key: gorse_key" \\
  -H "Content-Type: application/json" \\
  -d '[{
    "FeedbackType": "contact_agent",
    "UserId": "USER_ID",
    "ItemId": "ITEM_ID",
    "Timestamp": "UNIX_TIMESTAMP",
    "Comment": "weight:3.0"
  }]' \\
  http://localhost:8088/api/feedback

### Add new property listings
curl -X POST -H "X-API-Key: gorse_key" \\
  -H "Content-Type: application/json" \\
  -d '[{
    "ItemId": "NEW_ITEM_ID",
    "Timestamp": "UNIX_TIMESTAMP",
    "Labels": ["estate:ESTATE_NAME", "region:REGION_NAME"],
    "Categories": ["rental"],  # or ["sale"] or ["rental", "sale"]
    "Comment": "{\\"rent_price\\": 25000.0}"  # or sale_price
  }]' \\
  http://localhost:8088/api/items

# Integration
### **1 step:**
***Process Data***

1) Install realestate_data.csv

2) In terminal launch 

python process_data.py

(You will two new files with separated data: feedback.csv and item.csv)

### **2 step:**
***Start Docker containers***

***Start system***

docker-compose up -d

***Stop system***

docker-compose down

***View logs***

docker-compose logs -f gorse

***Restart***

docker-compose restart gorse

### ***3 step***
***upload data to gorse.io***

python upload_complete.py


## Configuration File (config.toml)

### Key settings for real estate:

```bash
[recommend.feedback_types]
positive_types = ["contact_agent"]  # Higher weight for contacting agent
read_types = ["view_listing"]       # Medium weight for viewing listings
positive_feedback_weight = 3.0
read_feedback_weight = 1.0

# Real estate categories
item_categories = ["rental", "sale", "rental|sale"]

# Real estate labels (for filtering/similarity)
item_labels = ["estate", "region"]



