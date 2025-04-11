# FILL THE LIST IN MAIN WITH URLS TO GET THE TEXT FROM

# NOTE: Some URLs block request connections. This script will not work on these types of URLs
# NOTE: This will generate a txt file with all text. Redundant text will need to be removed.


import requests
from bs4 import BeautifulSoup
# from youtube_transcript_api import YouTubeTranscriptApi
import re
import sys


def save_web_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status() # Check for HTTP request errrors

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)  # Extract visible text
        
        title = soup.title.string.strip() if soup.title else "Untitled"
        safe_title = re.sub(r'[\/:*?"<>|]', "_", title) # Removes invalid characters for file names
        filename = f"{safe_title}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)

    except requests.exceptions.RequestException as e:
        print(f"Error in {url}: {e}")


def main():
    articles = [
        # Fill this with valid urls to run
    ]

    for a in articles:
        save_web_text(a)


if __name__ == "__main__":
    main()
