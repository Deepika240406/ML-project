import os
import logging
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.datasets_path = Path(__file__).parent / 'datasets'
        self.database_available = False
        self._engine = None

        user = os.getenv('PGUSER')
        password = os.getenv('PGPASSWORD')
        host = os.getenv('PGHOST')
        port = os.getenv('PGPORT', '5432')
        database = os.getenv('PGDATABASE')

        # Check if real Postgres credentials are provided
        if user and password and host and database and 'your_neon_host' not in host and 'YOUR_DATABASE' not in database and host != 'localhost':
            try:
                from sqlalchemy import create_engine, text
                self._engine = create_engine(
                    f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{database}",
                    connect_args={'sslmode': os.getenv('PGSSLMODE', 'prefer'), 'connect_timeout': 5}
                )
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.database_available = True
                logger.info("Connected to database successfully.")
            except Exception as e:
                logger.warning(f"Database connection failed ({e}). Falling back to CSV datasets.")
                self.database_available = False
                self._engine = None
        else:
            logger.info("PostgreSQL credentials not configured or using default placeholders. Using CSV datasets.")

    def load_city_data(self, city):
        city = city.strip().title()
        if self.database_available and self._engine:
            try:
                from sqlalchemy import text
                with self._engine.connect() as conn:
                    df = pd.read_sql(
                        text("SELECT * FROM property_listings WHERE LOWER(city)=:city"),
                        conn, params={'city': city.lower()}
                    )
                if not df.empty:
                    df['city'] = city
                    df = self._clean_data(df)
                    logger.info(f"{city}: Loaded {len(df)} rows from database.")
                    return df
            except Exception as e:
                logger.warning(f"Failed to load {city} from database: {e}. Falling back to CSV.")

        # Fallback to CSV
        file_path = self.datasets_path / f"{city.lower()}_properties.csv"
        if not file_path.exists():
            logger.info(f"Data file not found for {city}: {file_path}")
            return pd.DataFrame()
        try:
            df = pd.read_csv(file_path)
            df['city'] = city
            df = self._clean_data(df)
            logger.info(f"{city}: Loaded {len(df)} valid rows from CSV.")
            return df
        except Exception as e:
            logger.error(f"Error reading CSV {file_path}: {e}")
            return pd.DataFrame()

    def load_all_data(self):
        if self.database_available and self._engine:
            try:
                from sqlalchemy import text
                with self._engine.connect() as conn:
                    df = pd.read_sql(text("SELECT * FROM property_listings"), conn)
                if not df.empty:
                    df = self._clean_data(df)
                    logger.info(f"Total rows loaded from database: {len(df)}")
                    return df
            except Exception as e:
                logger.warning(f"Failed to load data from database: {e}. Falling back to CSV.")

        cities = ['Mumbai', 'Delhi', 'Gurugram', 'Noida', 'Bangalore']
        all_data = []
        for city in cities:
            df = self.load_city_data(city)
            if not df.empty:
                all_data.append(df)
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            logger.info(f"Total valid rows loaded from CSV: {len(combined_data)}")
            return combined_data
        else:
            logger.warning("No valid data found. Please ensure CSV files are properly formatted.")
            return pd.DataFrame()

    def _clean_data(self, df):
        if df.empty:
            return df
        # Remove rows with missing critical values
        df = df.dropna(subset=['price', 'area_sqft', 'bhk'])
        # Coerce to numeric before applying range filters
        for col in ['price', 'area_sqft', 'bhk']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['price', 'area_sqft', 'bhk'])
        # Remove outliers (basic filtering)
        df = df[(df['price'] > 0) & (df['area_sqft'] > 0) & (df['bhk'] > 0)]
        # Cast to float64 for ML models
        for col in ['price', 'area_sqft', 'bhk']:
            df[col] = df[col].astype(np.float64)
        if 'city' in df.columns:
            df['city'] = df['city'].astype(str).str.strip().str.title()
        return df

    def get_data_summary(self):
        combined_data = self.load_all_data()
        if combined_data.empty:
            logger.debug("No valid data found for summary.")
            return None
        return combined_data.describe(include='all')

    def get_districts_by_city(self, city, combined_data=None):
        if combined_data is not None and not combined_data.empty:
            city_data = combined_data[combined_data['city'].str.lower() == str(city).lower()]
        else:
            city_data = self.load_city_data(city)
        if city_data.empty or 'district' not in city_data.columns:
            return []
        return sorted([str(d) for d in city_data['district'].dropna().unique()])

    def get_subdistricts_by_district(self, city, district, combined_data=None):
        if combined_data is not None and not combined_data.empty:
            city_data = combined_data[combined_data['city'].str.lower() == str(city).lower()]
        else:
            city_data = self.load_city_data(city)
        if city_data.empty or 'district' not in city_data.columns or 'sub_district' not in city_data.columns:
            return []
        sub_df = city_data[city_data['district'] == district]
        return sorted([str(sd) for sd in sub_df['sub_district'].dropna().unique()])