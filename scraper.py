from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

def scrape_clubs_selenium():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    url = "https://ucmerced.presence.io/organizations/list"
    all_clubs = []

    try:
        print(f"Navigating to {url}...")
        driver.get(url)

        wait = WebDriverWait(driver, 20)
        print("Waiting for table to render...")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "tbody")))

        # Try to set to 50 items per page
        try:
            rows_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".rows-per-page-btn")))
            rows_btn.click()
            option_50 = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "50")))
            option_50.click()
            time.sleep(3) 
            print("Successfully set view to 50.")
        except Exception:
            print("Could not set to 50 items, continuing with default...")

        page_num = 1
        
        # --- SAFE LOOP START ---
        print("\nNOTE: Press Ctrl+C at any time to STOP and SAVE data.\n")
        
        while True:
            try: 
                print(f"--- Scraping Page {page_num} ---")
                rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
                
                # Check if table is empty (sometimes happens on last page)
                if not rows:
                    print("No rows found. Ending.")
                    break

                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 5:
                            name = cells[0].text.strip()
                            if not name: continue 

                            club_data = {
                                "name": name,
                                "category": cells[1].text.strip(),
                                "meeting_time": cells[2].text.strip(),
                                "location": cells[3].text.strip(),
                                "member_count": cells[4].text.strip(),
                                "description": f"A {cells[1].text.strip()} organization at UC Merced."
                            }
                            all_clubs.append(club_data)
                    except Exception:
                        continue
                
                # Check for Next Button
                pagination_items = driver.find_elements(By.CSS_SELECTOR, "ul.pagination li")
                if pagination_items:
                    next_item = pagination_items[-1]
                    
                    if "disabled" in next_item.get_attribute("class"):
                        print("Reached the last page (button disabled).")
                        break
                    
                    link = next_item.find_element(By.TAG_NAME, "a")
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(3)
                    page_num += 1
                else:
                    print("No pagination found. Ending.")
                    break
            
            except KeyboardInterrupt:
                print("\n\n!!! STOPPING SCRAPER (User Interrupt) !!!")
                print("Saving data collected so far...")
                break  # Breaks the while loop but continues to return data
            
            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                break
        
        # --- SAFE LOOP END ---

    except Exception as e:
        print(f"Browser error: {e}")
    
    finally:
        driver.quit()

    return all_clubs

if __name__ == "__main__":
    clubs = scrape_clubs_selenium()
    
    if clubs:
        df = pd.DataFrame(clubs)
        df = df.drop_duplicates(subset=['name'])
        
        csv_filename = "scraped_clubs.csv"
        df.to_csv(csv_filename, index=False)
        print(f"\nSUCCESS! Saved {len(df)} clubs to '{csv_filename}'.")
    else:
        print("\nNo data was collected.")