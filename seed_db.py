import pandas as pd
from app import app, db
from models import Club

def seed_clubs():
    # Use the existing 'app' object to create the context
    with app.app_context():
        # 1. Read the CSV file
        try:
            print("Reading scraped_clubs.csv...")
            df = pd.read_csv('scraped_clubs.csv')
            
            # Fill "NaN" (empty) values with empty strings to prevent errors
            df = df.fillna('')
            
        except FileNotFoundError:
            print("Error: scraped_clubs.csv not found. Did you run the scraper?")
            return

        print(f"Found {len(df)} clubs. Seeding database...")

        # Optional: Clear existing clubs to avoid duplicates if re-seeding
        # Club.query.delete() 

        # 2. Iterate through the CSV rows
        for index, row in df.iterrows():
            # Check if club already exists to avoid duplicates
            existing_club = Club.query.filter_by(name=row['name']).first()
            
            if not existing_club:
                # Handle member_count safe conversion (e.g. turning "11" into 11, or "" into 0)
                count_val = 0
                if pd.notna(row['member_count']):
                    try:
                        # Convert to float first to handle cases like "11.0", then to int
                        count_val = int(float(row['member_count']))
                    except ValueError:
                        count_val = 0

                new_club = Club(
                    name=row['name'],
                    category=row['category'],
                    meeting_time=row['meeting_time'],
                    location=row['location'],
                    member_count=count_val,
                    description=row['description'],
                    verified=True  # <--- CRITICAL FIX: Sets scraped clubs as verified
                )
                
                db.session.add(new_club)
        
        # 3. Commit all changes
        try:
            db.session.commit()
            print("Database seeded successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_clubs()