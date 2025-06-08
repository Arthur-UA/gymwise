import argparse
import logging
from typing import List, Dict, Any

from scraper_client.client import ScraperClient  # Custom client for interacting with Apify

# Configure logging level
logging.basicConfig(level=logging.INFO)

def start_apify_scraper() -> None:
    """Starts the Apify scraper using a custom ScraperClient and logs the number of exercises retrieved."""
    logging.info('STARTING THE APIFY SCRAPER...')
    
    # Initialize the scraper client
    scraper_client: ScraperClient = ScraperClient()
    
    # Run the custom Apify actor and retrieve the exercises
    exercises: List[Dict[str, Any]] = scraper_client.run_custom_apify_actor()
    
    # Log the number of exercises obtained
    logging.info(f'SCRAPER JOB ENDED, {len(exercises)} TOTAL EXERCISES OBTAINED')

def main() -> None:
    """Parses command-line arguments and starts the scraping task if the corresponding flag is set."""
    parser = argparse.ArgumentParser(
        prog='GymWise control panel',
        description='Runs different services of GymWise application'
    )
    parser.add_argument(
        '--start-crawling',
        action='store_true',
        help='Starts Apify exercise scraping task'
    )
    
    # Parse command-line arguments
    args = parser.parse_args()

    # Trigger scraper if the flag is provided
    if args.start_crawling:
        start_apify_scraper()

if __name__ == '__main__':
    main()
