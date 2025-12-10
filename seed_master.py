import pandas as pd
from app import app, db
from models import Club, Post
from datetime import datetime, timedelta, timezone

def seed_everything():
    with app.app_context():
        print("1. Resetting Database...")
        db.drop_all()
        db.create_all()

        # --- STEP 2: LOAD CLUBS FROM CSV ---
        try:
            print("2. Loading Clubs from CSV...")
            df = pd.read_csv('scraped_clubs.csv')
            df = df.fillna('')
            
            for index, row in df.iterrows():
                # Check if exists (to prevent duplicates if run multiple times)
                if not Club.query.filter_by(name=row['name']).first():
                    
                    # Safe conversion for member count
                    count_val = 0
                    if row['member_count'] and str(row['member_count']).replace('.','',1).isdigit():
                         count_val = int(float(row['member_count']))

                    new_club = Club(
                        name=row['name'],
                        category=row['category'],
                        meeting_time=row['meeting_time'],
                        location=row['location'],
                        member_count=count_val,
                        description=row['description'],
                        verified=True # Auto-verify all scraped clubs
                    )
                    db.session.add(new_club)
            
            db.session.commit()
            print(f"   - Loaded {len(df)} clubs.")

        except FileNotFoundError:
            print("   - Warning: scraped_clubs.csv not found. Skipping CSV load.")

        # --- STEP 3: ADD MANUAL DEMO DATA (Machine Learning Club) ---
        print("3. Seeding Demo Posts...")
        
        # Find the club (It should exist from the CSV now)
        # We use 'ilike' to find it case-insensitively
        ml_club = Club.query.filter(Club.name.ilike("%Machine Learning%")).first()
        
        if ml_club:
            print(f"   - Found {ml_club.name}, adding posts...")
            
            # Post 1: General Social Post
            post1 = Post(
                club_id=ml_club.id,
                image_file="ml_social.jpg", 
                caption="Great vibes at our social yesterday! 🍕 Thanks for coming out.",
                is_event=False,
                created_at=datetime.now(timezone.utc) - timedelta(days=2)
            )

            # Post 2: Upcoming Event
            event1 = Post(
                club_id=ml_club.id,
                image_file="ml_workshop.jpg",
                caption="Join us for an Intro to Neural Networks! Beginners welcome.",
                is_event=True,
                event_title="Neural Networks 101",
                event_date=datetime.now(timezone.utc) + timedelta(days=5),
                event_location="COB2 140",
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(post1)
            db.session.add(event1)
            db.session.commit()
            print("   - Posts added!")
        else:
            print("   - Error: Machine Learning Club not found in CSV data.")

        print("Done! Database is ready.")

if __name__ == "__main__":
    seed_everything()