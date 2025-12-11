#!/usr/bin/env python3
"""
Movie Scraper - Scrapes movie data from ssr1.scrape.center
Extracts: Movie Name, Image URL, Rating, and Genre
Saves data to movie.csv

Uses Selenium to handle JavaScript-rendered content
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import csv
import time
from typing import List, Dict
from urllib.parse import urljoin

# Base URL for the scraper
BASE_URL = "https://ssr1.scrape.center"

def init_driver():
    """Initialize Selenium WebDriver with Chrome"""
    options = Options()
    # Uncomment for headless mode (faster):
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_movies(num_pages: int = 10) -> List[Dict]:
    """
    Scrapes movie data from multiple pages using Selenium.
    
    Args:
        num_pages: Number of pages to scrape (default: 10)
        
    Returns:
        List of dictionaries containing movie data
    """
    movies = []
    
    for page_num in range(1, num_pages + 1):
        url = f"{BASE_URL}/page/{page_num}"
        
        print(f"Scraping page {page_num}: {url}")
        
        driver = None
        try:
            # Create a fresh driver for each page to avoid session issues
            driver = init_driver()
            driver.get(url)
            
            # Wait for movie items to load (max 10 seconds)
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "item")))
            
            # Parse the rendered HTML
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all movie containers
            movie_items = soup.find_all('div', class_='item')
            
            if not movie_items:
                print(f"  ⚠ No movie items found on page {page_num}")
            
            for item in movie_items:
                try:
                    # Extract image URL first (more reliable)
                    img_elem = item.find('img')
                    image_url = "N/A"
                    if img_elem and img_elem.get('src'):
                        image_url = img_elem['src']
                        if image_url and not image_url.startswith('http'):
                            image_url = urljoin(BASE_URL, image_url)
                    
                    # Extract movie name from the link or title attribute
                    name_elem = item.find('a', class_='name')
                    if not name_elem:
                        name_elem = item.find('a')
                    
                    movie_name = "N/A"
                    if name_elem:
                        if name_elem.get('title'):
                            movie_name = name_elem['title'].strip()
                        else:
                            movie_name = name_elem.get_text(strip=True)
                    
                    # Extract rating
                    rating_elem = item.find('p', class_='score')
                    rating = "N/A"
                    if rating_elem:
                        rating = rating_elem.get_text(strip=True)
                    
                    # Extract genre from the category buttons
                    genre = "N/A"
                    categories = item.find_all('button', class_='category')
                    if categories:
                        genre_list = [cat.get_text(strip=True) for cat in categories]
                        genre = ' '.join(genre_list)
                    
                    # Only add if we have at least a valid image
                    if image_url != "N/A":
                        movies.append({
                            'name': movie_name,
                            'image_url': image_url,
                            'rating': rating,
                            'genre': genre
                        })
                        
                        print(f"  ✓ Found: {movie_name} (Rating: {rating})")
                    
                except Exception as e:
                    print(f"  ⚠ Error parsing movie item: {e}")
                    continue
            
            # Be respectful - add delay between requests
            if page_num < num_pages:
                time.sleep(1)
                
        except Exception as e:
            print(f"  ✗ Error scraping page {page_num}: {e}")
            continue
        finally:
            # Always close the driver after each page
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    return movies


def save_to_csv(movies: List[Dict], filename: str = 'movie.csv'):
    """
    Saves movie data to CSV file.
    
    Args:
        movies: List of movie dictionaries
        filename: Output CSV filename
    """
    if not movies:
        print("No movies to save!")
        return
    
    fieldnames = ['name', 'image_url', 'rating', 'genre']
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data
            writer.writerows(movies)
        
        print(f"\n✓ Successfully saved {len(movies)} movies to {filename}")
        
    except IOError as e:
        print(f"✗ Error saving to CSV: {e}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("Movie Scraper - ssr1.scrape.center")
    print("=" * 60)
    
    # Scrape 10 pages
    movies = scrape_movies(num_pages=10)
    
    print(f"\n{'=' * 60}")
    print(f"Total movies scraped: {len(movies)}")
    print(f"{'=' * 60}")
    
    # Save to CSV
    save_to_csv(movies)
    
    # Display sample data
    if movies:
        print("\nSample data (first 3 movies):")
        print("-" * 60)
        for i, movie in enumerate(movies[:3], 1):
            print(f"\n{i}. {movie['name']}")
            print(f"   Rating: {movie['rating']}")
            print(f"   Genre: {movie['genre']}")
            print(f"   Image: {movie['image_url']}")


if __name__ == "__main__":
    main()
