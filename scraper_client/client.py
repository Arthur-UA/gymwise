import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Define the base directory for scraper-related files
MODULE_DIR = Path('scraper_client')


class ScraperClient:
    """Handles interaction with the Apify platform for scraping exercise data."""

    def __init__(self) -> None:
        """Initializes the Apify client with the API key from environment variables."""
        self.client = ApifyClient(os.environ['APIFY_KEY'])

    def run_custom_apify_actor(self, output_path: Optional[str] = 'scraper_output.json') -> List[Dict[str, Any]]:
        """Runs a custom Apify actor to scrape data and optionally saves the result to a JSON file.

        Args:
            output_path (str): Optional name of the file where the scraped data will be saved.

        Returns:
            output (List[Dict[str, Any]]): A list of dictionaries representing the scraped exercise data.
        """
        # Input settings for the Apify actor run
        run_input: Dict[str, Any] = {
            "runMode": "DEVELOPMENT",
            "startUrls": [{"url": "https://www.jefit.com/exercises"}],
            "keepUrlFragments": False,
            "respectRobotsTxtFile": True,
            "linkSelector": 'a[aria-label="Next page"]',
            "globs": [],
            "pseudoUrls": [{"purl": "https://www.jefit.com/exercises?page=[\\d+]"}],
            "excludes": [],
            "injectJQuery": True,
            "proxyConfiguration": {"useApifyProxy": True},
            "proxyRotation": "RECOMMENDED",
            "initialCookies": [],
            "useChrome": False,
            "headless": True,
            "ignoreSslErrors": False,
            "ignoreCorsAndCsp": False,
            "downloadMedia": True,
            "downloadCss": True,
            "maxRequestRetries": 3,
            "maxPagesPerCrawl": 0,
            "maxResultsPerCrawl": 0,
            "maxCrawlingDepth": 0,
            "maxConcurrency": 50,
            "pageLoadTimeoutSecs": 60,
            "pageFunctionTimeoutSecs": 60,
            "waitUntil": ["networkidle2"],
            "preNavigationHooks": """// We need to return array of (possibly async) functions here.
        // The functions accept two arguments: the \"crawlingContext\" object
        // and \"gotoOptions\".
        [
            async (crawlingContext, gotoOptions) => {
                // ...
            },
        ]
        """,
            "postNavigationHooks": """// We need to return array of (possibly async) functions here.
        // The functions accept a single argument: the \"crawlingContext\" object.
        [
            async (crawlingContext) => {
                // ...
            },
        ]""",
            "breakpointLocation": "NONE",
            "closeCookieModals": False,
            "maxScrollHeightPixels": 5000,
            "debugLog": False,
            "browserLog": False,
            "customData": {},
        }

        # Load the custom page function JavaScript from a file
        with open(MODULE_DIR / 'page_function.js', 'r') as file:
            page_function: str = file.read()
            run_input['pageFunction'] = page_function

        # Run the actor and collect the result
        run: Dict[str, Any] = self.client.actor("moJRLRc85AitArpNN").call(run_input=run_input)
        output: List[Dict[str, Any]] = self._parse_data(run)

        # Optionally save the output to a JSON file
        if output_path:
            with open(MODULE_DIR / output_path, 'w') as file:
                json.dump(output, file, indent=4)

        return output

    def _parse_data(self, run_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieves and parses dataset items from a completed Apify actor run.

        Args:
            run_result: The dictionary containing the actor run metadata.

        Returns:
            A list of dictionaries representing the dataset items.
        """
        return list(self.client.dataset(run_result["defaultDatasetId"]).iterate_items())
