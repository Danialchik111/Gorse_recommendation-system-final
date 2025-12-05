import pandas as pd
import json
import ast
from datetime import datetime
import os
from pathlib import Path
import traceback

class RealEstateDataProcessor:
    def __init__(self, input_csv_path):
        self.input_csv_path = input_csv_path
        self.df = None
        self.feedback_df = None
        self.items_df = None
        self.users_df = None
        
    def safe_json_parse(self, json_str):
        if pd.isna(json_str):
            return None
            
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
            
        try:
            return ast.literal_eval(json_str)
        except (ValueError, SyntaxError):
            pass
            
        try:
            cleaned = json_str.replace('\\"', '"').replace('"{', '{').replace('}"', '}')
            return json.loads(cleaned)
        except:
            pass
            
        print(f"Warning: Could not parse JSON: {json_str[:100]}...")
        return None
    
    def load_data(self):
        print(f"Loading data from {self.input_csv_path}...")
        
        try:
            with open(self.input_csv_path, 'r') as f:
                first_lines = [next(f) for _ in range(3)]
            print("First few lines of CSV:")
            for i, line in enumerate(first_lines):
                print(f"Line {i}: {line[:200]}...")
        except Exception as e:
            print(f"Could not preview file: {e}")
        
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    print(f"Trying encoding: {encoding}")
                    self.df = pd.read_csv(self.input_csv_path, encoding=encoding)
                    print(f"Successfully loaded with {encoding} encoding")
                    print(f"Columns: {list(self.df.columns)}")
                    print(f"First row sample:")
                    print(self.df.iloc[0].to_dict())
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print("Failed to load with any encoding")
                return False
                
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
        
        print("\nParsing event_property column...")
        parse_errors = 0
        
        def parse_row(value):
            nonlocal parse_errors
            try:
                result = self.safe_json_parse(value)
                if result is None:
                    parse_errors += 1
                return result
            except Exception as e:
                parse_errors += 1
                print(f"Parse error for value: {value[:50] if value else 'None'}... Error: {e}")
                return None
        
        self.df['event_property_parsed'] = self.df['event_property'].apply(parse_row)
        
        if parse_errors > 0:
            print(f"Warning: {parse_errors} rows could not be parsed")
        
        self._extract_properties()
        
        print(f"\nLoaded {len(self.df)} rows of data")
        print(f"Unique users: {self.df['user_id'].nunique()}")
        print(f"Unique properties found: {self.df['house_id'].nunique()}")
        
        print("\nSample parsed data:")
        for i in range(min(3, len(self.df))):
            row = self.df.iloc[i]
            print(f"Row {i}: User={row['user_id']}, Event={row['event_name']}, Property={row.get('house_id', 'N/A')}")
        
        return True
    
    def _extract_properties(self):
        print("\nExtracting properties...")
        
        self.df['house_id'] = None
        properties_to_extract = [
            'pageType', 'rent_price', 'sale_price', 
            'estate_name', 'region_name', 'house_address'
        ]
        
        for prop in properties_to_extract:
            self.df[prop] = None
        
        for idx, row in self.df.iterrows():
            parsed = row['event_property_parsed']
            
            if isinstance(parsed, dict):
                self.df.at[idx, 'house_id'] = parsed.get('house_id')
                
                for prop in properties_to_extract:
                    self.df.at[idx, prop] = parsed.get(prop)
        
        print("Cleaning data types...")
        
        self.df['rent_price'] = pd.to_numeric(self.df['rent_price'], errors='coerce')
        self.df['sale_price'] = pd.to_numeric(self.df['sale_price'], errors='coerce')
        
        try:
            self.df['created_at'] = pd.to_datetime(self.df['created_at'], errors='coerce')
            self.df['timestamp'] = self.df['created_at'].apply(
                lambda x: int(x.timestamp()) if pd.notnull(x) else 0
            )
        except Exception as e:
            print(f"Warning: Could not parse timestamps: {e}")
            self.df['timestamp'] = 0
        
        print(f"\nExtraction Summary:")
        print(f"  Valid house_id entries: {self.df['house_id'].notna().sum()}")
        print(f"  Properties with rent_price: {self.df['rent_price'].notna().sum()}")
        print(f"  Properties with sale_price: {self.df['sale_price'].notna().sum()}")
    
    def create_feedback_data(self, output_path='feedback.csv'):
        print("\nCreating feedback data...")
        
        if 'house_id' not in self.df.columns or self.df['house_id'].isna().all():
            print("Error: No house_id data found")
            return None
        
        valid_rows = self.df[self.df['house_id'].notna()].copy()
        
        if len(valid_rows) == 0:
            print("Error: No valid rows with house_id")
            return None
        
        feedback_data = []
        feedback_weights = {
            'view_listing': 1.0,
            'contact_agent': 3.0
        }
        
        for _, row in valid_rows.iterrows():
            feedback_entry = {
                'feedback_type': row['event_name'],
                'user_id': str(row['user_id']),
                'item_id': str(row['house_id']),
                'timestamp': int(row.get('timestamp', 0)),
                'comment': f"weight:{feedback_weights.get(row['event_name'], 1.0)}"
            }
            feedback_data.append(feedback_entry)
        
        self.feedback_df = pd.DataFrame(feedback_data)
        
        self.feedback_df.to_csv(output_path, index=False)
        print(f"✓ Feedback data saved to {output_path}")
        print(f"  Total entries: {len(self.feedback_df)}")
        print(f"  Feedback types:")
        for feedback_type, count in self.feedback_df['feedback_type'].value_counts().items():
            print(f"    - {feedback_type}: {count}")
        
        return output_path
    
    def create_item_data(self, output_path='items.csv'):
        print("\nCreating item data...")
        
        if 'house_id' not in self.df.columns:
            print("Error: house_id column not found")
            return None
        
        unique_properties = self.df.dropna(subset=['house_id']).drop_duplicates('house_id')
        
        if len(unique_properties) == 0:
            print("Error: No unique properties found")
            return None
        
        item_data = []
        
        for _, row in unique_properties.iterrows():
            listing_type = []
            if pd.notna(row['rent_price']) and row['rent_price'] > 0:
                listing_type.append('rental')
            if pd.notna(row['sale_price']) and row['sale_price'] > 0:
                listing_type.append('sale')
            
            labels = []
            if pd.notna(row['estate_name']):
                labels.append(f"estate:{row['estate_name']}")
            if pd.notna(row['region_name']):
                labels.append(f"region:{row['region_name']}")
            
            numerical_features = {}
            if pd.notna(row['rent_price']) and row['rent_price'] > 0:
                numerical_features['rent_price'] = float(row['rent_price'])
            if pd.notna(row['sale_price']) and row['sale_price'] > 0:
                numerical_features['sale_price'] = float(row['sale_price'])
            
            item_entry = {
                'item_id': str(row['house_id']),
                'timestamp': int(row.get('timestamp', 0)),
                'labels': '|'.join(labels) if labels else '',
                'categories': '|'.join(listing_type) if listing_type else '',
                'comment': json.dumps(numerical_features, ensure_ascii=False)
            }
            item_data.append(item_entry)
        
        self.items_df = pd.DataFrame(item_data)
        
        self.items_df.to_csv(output_path, index=False)
        print(f"✓ Item data saved to {output_path}")
        print(f"  Total unique properties: {len(self.items_df)}")
        print(f"  Properties with labels: {self.items_df['labels'].ne('').sum()}")
        
        return output_path
    
    def create_user_data(self, output_path='users.csv'):
        print("\nCreating user data...")
        
        unique_users = self.df['user_id'].dropna().unique()
        
        user_data = []
        for user_id in unique_users:
            user_entry = {
                'user_id': str(user_id),
                'labels': '',
                'comment': ''
            }
            user_data.append(user_entry)
        
        self.users_df = pd.DataFrame(user_data)
        
        self.users_df.to_csv(output_path, index=False)
        print(f"✓ User data saved to {output_path}")
        print(f"  Total unique users: {len(self.users_df)}")
        
        return output_path
    
    def debug_data(self):
        print("\n" + "="*60)
        print("DATA DEBUG INFO")
        print("="*60)
        
        print(f"\nDataFrame shape: {self.df.shape}")
        print(f"\nColumns: {list(self.df.columns)}")
        
        print(f"\nFirst few rows of event_property:")
        for i in range(min(5, len(self.df))):
            prop = self.df.iloc[i]['event_property']
            print(f"Row {i}: {str(prop)[:200]}...")
        
        print(f"\nData types:")
        print(self.df.dtypes)
        
        print(f"\nMissing values:")
        print(self.df.isnull().sum())
        
        print(f"\nUnique event names:")
        print(self.df['event_name'].value_counts())
        
        if 'house_id' in self.df.columns:
            print(f"\nSample house_id values:")
            print(self.df['house_id'].head(10).tolist())


def main():
    
    INPUT_CSV = 'realestate_data.csv'
    
    if not os.path.exists(INPUT_CSV):
        print(f"❌ File not found: {INPUT_CSV}")
        print("Please ensure the CSV file is in the current directory.")
        return
    
    output_dir = 'gorse_data'
    Path(output_dir).mkdir(exist_ok=True)
    
    processor = RealEstateDataProcessor(INPUT_CSV)
    
    print("="*60)
    print("STEP 1: DEBUG DATA")
    print("="*60)
    
    if not processor.load_data():
        print("Failed to load data. Running debug...")
        try:
            df_raw = pd.read_csv(INPUT_CSV)
            print(f"\nRaw DataFrame loaded. Shape: {df_raw.shape}")
            print(f"Columns: {list(df_raw.columns)}")
            print(f"\nFirst row:")
            print(df_raw.iloc[0].to_dict())
            
            print(f"\nSample of event_property column:")
            for i in range(min(3, len(df_raw))):
                print(f"Row {i}: {df_raw.iloc[i]['event_property'][:200]}...")
        except Exception as e:
            print(f"Could not load raw data: {e}")
        return
    
    processor.debug_data()
    
    print("\n" + "="*60)
    print("STEP 2: CREATE GORSE DATA FILES")
    print("="*60)
    
    try:
        feedback_file = os.path.join(output_dir, 'feedback.csv')
        items_file = os.path.join(output_dir, 'items.csv')
        users_file = os.path.join(output_dir, 'users.csv')
        
        feedback_success = processor.create_feedback_data(feedback_file)
        items_success = processor.create_item_data(items_file)
        users_success = processor.create_user_data(users_file)
        
        if feedback_success and items_success and users_success:
            print("\n" + "="*60)
            print("✅ SUCCESS!")
            print("="*60)
            print(f"\nCreated files in '{output_dir}/':")
            print(f"1. feedback.csv - {len(processor.feedback_df)} interactions")
            print(f"2. items.csv - {len(processor.items_df)} properties")
            print(f"3. users.csv - {len(processor.users_df)} users")
            
            print(f"\nCreating test_sample.csv with 10 rows for quick testing...")
            if processor.feedback_df is not None and len(processor.feedback_df) > 10:
                processor.feedback_df.head(10).to_csv(
                    os.path.join(output_dir, 'test_sample.csv'), 
                    index=False
                )
                print("✓ Created test_sample.csv")
        else:
            print("\n❌ Failed to create one or more files")
            
    except Exception as e:
        print(f"\n❌ Error creating files: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
