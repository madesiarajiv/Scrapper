import os
import time
import pandas as pd
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up WebDriver with Chrome options
chrome_options = webdriver.ChromeOptions()

# Configure Chrome to use its default Downloads directory
prefs = {
    "download.default_directory": "",  # Leave empty for Chrome's default Downloads folder
    "download.prompt_for_download": False,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
wait = WebDriverWait(driver, 10)

def search_google_maps(query, max_results=10000):
    try:
        driver.get("https://www.google.com/maps")  # Open Google Maps
        wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))

        # Enter the search query automatically
        search_box = driver.find_element(By.ID, "searchboxinput")
        search_box.send_keys(query)  # Automatically enters the query into the search box
        search_box.send_keys("\n")
        time.sleep(5)

        results = []
        last_scroll_height = 0
        retries = 0

        while len(results) < max_results:
            # Wait for result cards to load
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.bfdHYd")))

            places = driver.find_elements(By.CSS_SELECTOR, "div.bfdHYd")
            print(f"Found {len(places)} places so far...")

            for place in places:
                try:
                    # Extract the name
                    name = place.find_element(By.CSS_SELECTOR, "div.qBF1Pd").text
                except:
                    name = "N/A"

                try:
                    # Extract the rating
                    rating = place.find_element(By.CSS_SELECTOR, "span.ZkP5Je").get_attribute("aria-label")
                    rating = rating.split(" ")[0] if rating else "N/A"
                except:
                    rating = "N/A"

                try:
                    # Extract the number of reviews
                    reviews = place.find_element(By.CSS_SELECTOR, "span.UY7F9").text
                except:
                    reviews = "N/A"

                try:
                    # Extract the category
                    category = place.find_element(By.XPATH, ".//div[contains(@class, 'W4Efsd')]/span[1]/span").text
                except:
                    category = "N/A"

                try:
                    # Extract the address
                    address = place.find_element(By.XPATH, ".//span[contains(text(), ',')]").text
                except:
                    address = "N/A"

                try:
                    # Extract the phone number
                    phone = place.find_element(By.CSS_SELECTOR, "span.UsdlK").text
                except:
                    phone = "N/A"

                results.append({
                    "Name": name,
                    "Phone": phone,
                    "Category": category,
                    "Address": address,
                    "Reviews": reviews,
                    "Rating": rating,
                })

                # Stop if we reach the maximum desired results
                if len(results) >= max_results:
                    break

            # Scroll to load more results
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Check if new data has been loaded
            new_scroll_height = driver.execute_script("return document.body.scrollHeight;")
            if new_scroll_height == last_scroll_height:
                retries += 1
                if retries > 5:  # Stop if no new data is loaded after 5 retries
                    print("No more results to load.")
                    break
            else:
                retries = 0

            last_scroll_height = new_scroll_height

        return results

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        driver.quit()

# Remove duplicates based on specified keys
def remove_duplicates(data):
    df = pd.DataFrame(data)
    # Keep only unique rows based on 'Name' and 'Address'
    df = df.drop_duplicates(subset=["Name", "Address"], keep="first")
    return df

# Function to get a unique file name if the file already exists
def get_unique_filename(directory, base_name):
    """
    Generate a unique file name by appending a numeric suffix if the file already exists.
    """
    name, ext = os.path.splitext(base_name)
    counter = 1
    unique_name = base_name

    while os.path.exists(os.path.join(directory, unique_name)):
        unique_name = f"{name}{counter}{ext}"
        counter += 1

    return unique_name

# Main function
def main():
    # Wait for user input for the query
    query = input("Enter your search query for Google Maps: ")
    if not query.strip():
        print("Search query cannot be empty. Please try again.")
        return

    print("Opening Google Maps and searching for the query...")

    data = search_google_maps(query, max_results=10000)

    if data:
        # Remove duplicates
        df = remove_duplicates(data)

        # Specify the directory and base file name
        downloads_dir = os.path.expanduser("~/Downloads")
        base_name = "google_maps_data.csv"

        # Get a unique file name
        unique_file_name = get_unique_filename(downloads_dir, base_name)

        # Save the file
        file_path = os.path.join(downloads_dir, unique_file_name)

        try:
            df.to_csv(file_path, index=False)
            print(f"Data saved to {file_path} with {len(df)} unique records.")
        except PermissionError as e:
            print(f"Permission denied: {e}. Please check file permissions or ensure the file isn't open.")
    else:
        print("No data was scraped. Please check the script or query.")

if __name__ == "__main__":
    main()
