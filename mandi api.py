import requests
import json
import pandas as pd
from datetime import datetime
import time

class MandiPriceAPI:
    def __init__(self, api_key):
        """
        Initialize the Mandi Price API client
        
        Args:
            api_key (str): Your API key from data.gov.in
        """
        self.api_key = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
        self.api_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    
    def fetch_commodity_prices(self, limit=100, offset=0, filters=None):
        """
        Fetch commodity prices from Indian mandi markets
        
        Args:
            limit (int): Number of records to fetch (default: 100)
            offset (int): Starting point for pagination (default: 0)
            filters (dict): Optional filters for state, district, market, commodity, etc.
        
        Returns:
            list: List of commodity price records
        """
        params = {
            'api-key': self.api_key,
            'format': 'json',
            'limit': limit,
            'offset': offset
        }
        
        # Add filters if provided
        if filters:
            for key, value in filters.items():
                params[f'filters[{key}]'] = value
        
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'records' in data:
                return data['records']
            else:
                print("No records found in response")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def get_filtered_prices(self, **kwargs):
        """
        Get filtered commodity prices
        
        Available filters:
        - state: State name (e.g., "Gujarat", "Punjab")
        - district: District name
        - market: Market name
        - commodity: Commodity name (e.g., "Cotton", "Wheat", "Rice")
        - variety: Variety of commodity
        - grade: Grade of commodity
        """
        return self.fetch_commodity_prices(filters=kwargs)
    
    def get_commodity_by_name(self, commodity_name, limit=50):
        """
        Get prices for a specific commodity
        
        Args:
            commodity_name (str): Name of the commodity
            limit (int): Number of records to fetch
        """
        return self.fetch_commodity_prices(
            limit=limit, 
            filters={'commodity': commodity_name}
        )
    
    def get_state_prices(self, state_name, limit=50):
        """
        Get prices for a specific state
        
        Args:
            state_name (str): Name of the state
            limit (int): Number of records to fetch
        """
        return self.fetch_commodity_prices(
            limit=limit,
            filters={'state': state_name}
        )
    
    def display_prices(self, records, show_count=10):
        """
        Display commodity prices in a formatted way
        """
        if not records:
            print("No data to display")
            return
        
        print(f"\n{'='*80}")
        print(f"MANDI COMMODITY PRICES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        for i, record in enumerate(records[:show_count]):
            print(f"\n{i+1}. {record['commodity']} - {record['variety']}")
            print(f"   Location: {record['market']}, {record['district']}, {record['state']}")
            print(f"   Date: {record['arrival_date']}")
            print(f"   Price Range: ₹{record['min_price']} - ₹{record['max_price']}")
            print(f"   Modal Price: ₹{record['modal_price']} ({record['grade']})")
        
        if len(records) > show_count:
            print(f"\n... and {len(records) - show_count} more records")
    
    def save_to_csv(self, records, filename=None):
        """
        Save commodity data to CSV file
        """
        if not records:
            print("No data to save")
            return None
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"mandi_prices_{timestamp}.csv"
        
        df = pd.DataFrame(records)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        return filename
    
    def get_price_summary(self, records):
        """
        Get summary statistics for the fetched prices
        """
        if not records:
            return None
        
        df = pd.DataFrame(records)
        
        # Convert price columns to numeric
        price_cols = ['min_price', 'max_price', 'modal_price']
        for col in price_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        summary = {
            'total_records': len(records),
            'unique_commodities': df['commodity'].nunique(),
            'unique_states': df['state'].nunique(),
            'unique_markets': df['market'].nunique(),
            'latest_date': df['arrival_date'].max(),
            'price_range': {
                'min_modal_price': df['modal_price'].min(),
                'max_modal_price': df['modal_price'].max(),
                'avg_modal_price': df['modal_price'].mean()
            }
        }
        
        return summary

# =============================================================================
# MAIN USAGE SCRIPT - JUST PASTE YOUR API KEY BELOW
# =============================================================================

def main():
    # 🔑 PASTE YOUR API KEY HERE
    API_KEY = "YOUR_API_KEY_HERE"
    
    # Initialize the API client
    mandi_api = MandiPriceAPI(API_KEY)
    
    print("🌾 MANDI COMMODITY PRICE FETCHER 🌾")
    print("=" * 50)
    
    # Example 1: Get latest 20 commodity prices
    print("\n1. Latest 20 Commodity Prices:")
    latest_prices = mandi_api.fetch_commodity_prices(limit=20)
    if latest_prices:
        mandi_api.display_prices(latest_prices, show_count=5)
    
    # Example 2: Get cotton prices
    print("\n2. Cotton Prices:")
    cotton_prices = mandi_api.get_commodity_by_name("Cotton", limit=10)
    if cotton_prices:
        mandi_api.display_prices(cotton_prices, show_count=3)
    
    # Example 3: Get prices for a specific state (Gujarat)
    print("\n3. Gujarat State Prices:")
    gujarat_prices = mandi_api.get_state_prices("Gujarat", limit=10)
    if gujarat_prices:
        mandi_api.display_prices(gujarat_prices, show_count=3)
    
    # Example 4: Get filtered prices
    print("\n4. Wheat prices in Punjab:")
    wheat_punjab = mandi_api.get_filtered_prices(
        commodity="Wheat",
        state="Punjab"
    )
    if wheat_punjab:
        mandi_api.display_prices(wheat_punjab, show_count=3)
    
    # Example 5: Save data to CSV
    print("\n5. Saving data to CSV:")
    if latest_prices:
        csv_file = mandi_api.save_to_csv(latest_prices)
        
        # Show summary
        summary = mandi_api.get_price_summary(latest_prices)
        if summary:
            print(f"\nData Summary:")
            print(f"- Total Records: {summary['total_records']}")
            print(f"- Unique Commodities: {summary['unique_commodities']}")
            print(f"- Unique States: {summary['unique_states']}")
            print(f"- Latest Date: {summary['latest_date']}")
            print(f"- Price Range: ₹{summary['price_range']['min_modal_price']:.0f} - ₹{summary['price_range']['max_modal_price']:.0f}")

# =============================================================================
# SIMPLE FUNCTIONS FOR QUICK USE
# =============================================================================

def quick_fetch(api_key, commodity=None, state=None, limit=20):
    """
    Quick function to fetch prices with minimal setup
    
    Usage:
        data = quick_fetch("your_api_key", commodity="Rice", limit=10)
    """
    api = MandiPriceAPI(api_key)
    
    filters = {}
    if commodity:
        filters['commodity'] = commodity
    if state:
        filters['state'] = state
    
    if filters:
        return api.fetch_commodity_prices(limit=limit, filters=filters)
    else:
        return api.fetch_commodity_prices(limit=limit)

def show_commodities(api_key, limit=50):
    """
    Show available commodities in the system
    """
    api = MandiPriceAPI(api_key)
    records = api.fetch_commodity_prices(limit=limit)
    
    if records:
        commodities = set(record['commodity'] for record in records)
        print("Available Commodities:")
        for i, commodity in enumerate(sorted(commodities), 1):
            print(f"{i}. {commodity}")
        return list(commodities)
    
    return []

# Run the main function
if __name__ == "__main__":
    main()
