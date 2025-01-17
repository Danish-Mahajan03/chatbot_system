import requests
import time
from tqdm import tqdm

# YOUTUBE_API_KEY = 'AIzaSyCEB7ugzZS9dJVnOKeRUXo4ewM2i1rIFLo'

class VideoExtractor:
    """
    A class to extract video metadata from YouTube using the YouTube API, 
    and extract video URLs from iframes and anchor tags in an HTML page.

    Attributes:
        YOUTUBE_API_KEY (str): The API key for accessing YouTube Data API.
        driver (WebDriver): The WebDriver instance for the current browser session.
    """

    def __init__(self, driver):
        """
        Initializes the VideoExtractor with the provided YouTube API key and WebDriver.

        Args:
            youtube_api_key (str): The API key for accessing YouTube Data API.
            driver (WebDriver): The WebDriver instance for the current browser session.
        """
        self.__YOUTUBE_API_KEY = 'AIzaSyCEB7ugzZS9dJVnOKeRUXo4ewM2i1rIFLo', 
        self.__driver = driver


    def __fetch_youtube_metadata(self, video_id):
        """
        Fetches metadata for a YouTube video by its ID using the YouTube Data API.

        Args:
            video_id (str): The ID of the YouTube video.

        Returns:
            dict: A dictionary containing the video metadata such as title, description, 
                  tags, upload date, view count, like count, etc.
                  Returns an empty dictionary if an error occurs.
        """

        url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={video_id}&key={self.__YOUTUBE_API_KEY}'
        response = requests.get(url)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'items' in data and data['items']:
                    item = data['items'][0]
                    snippet = item.get('snippet', {})
                    stats = item.get('statistics', {})
                    content_details = item.get('contentDetails', {})
                    
                    return {
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'tags': snippet.get('tags', []),
                        'upload_date': snippet.get('publishedAt', ''),
                        'channel_title': snippet.get('channelTitle', ''),
                        'view_count': stats.get('viewCount', '0'),
                        'like_count': stats.get('likeCount', '0'),
                        'dislike_count': stats.get('dislikeCount', '0'),
                        'duration': content_details.get('duration', ''),
                        'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                        'category': snippet.get('categoryId', ''),
                        'channel_id': snippet.get('channelId', ''),
                    }
            except ValueError as e:
                print(f"Error parsing JSON for video ID {video_id}: {e}")
        else:
            print(f"Error fetching metadata for video ID {video_id}: {response.status_code}")
        
        return {}


    def extract_video_iframes_and_links(self, soup):
        """
        Extracts video information from an HTML page, including video metadata 
        from YouTube embedded iframes and links.

        This method checks both `<iframe>` and `<a>` tags in the parsed HTML content 
        for YouTube video IDs and related metadata. It collects video details such as 
        title, description, view count, and other statistics using the YouTube API.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML page.

        Returns:
            dict: A dictionary containing two keys:
                - 'videos_from_iframes': A list of dictionaries with metadata for each embedded YouTube video.
                - 'video_links_data': A list of dictionaries with metadata for video links (e.g., YouTube, Vimeo).
        """  

        video_data = []
        iframes = soup.find_all('iframe')

        for iframe in tqdm(iframes, desc="Processing iframes"):
            iframe_src = iframe.get('src')
            if iframe_src and 'youtube.com/embed/' in iframe_src:
                video_dict = {}
                video_dict['iframe_url'] = iframe_src
                video_id = iframe_src.split('/embed/')[1].split('?')[0]
                video_dict['video_id'] = video_id
                youtube_metadata = self.__fetch_youtube_metadata(video_id)
                video_dict.update(youtube_metadata)
                video_dict['source_page'] = self.__driver.current_url
                video_dict['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
                video_dict['width'] = iframe.get('width')
                video_dict['height'] = iframe.get('height')
                video_dict['allow'] = iframe.get('allow')
                video_data.append(video_dict)

        anchor_tags = soup.find_all('a')
        video_links_data = []
        for anchor in tqdm(anchor_tags, desc="Processing anchor tags containing video href"):
            href = anchor.get('href')
            if href:
                if 'youtube.com/watch' in href or 'youtu.be/' in href or 'vimeo.com' in href or href.endswith(('.mp4', '.avi', '.mov')):
                    if 'youtube.com/watch' in href:
                        video_id = href.split('v=')[-1].split('&')[0]
                        youtube_metadata = self.__fetch_youtube_metadata(video_id)
                        video_metadata_dict = {
                            'video_link': href,
                            **youtube_metadata
                        }
                        video_links_data.append(video_metadata_dict)
                    elif 'youtu.be/' in href:
                        video_id = href.split('/')[-1]
                        youtube_metadata = self.__fetch_youtube_metadata(video_id)
                        video_metadata_dict = {
                            'video_link': href,
                            **youtube_metadata
                        }
                        video_links_data.append(video_metadata_dict)
                    else:
                        video_links_data.append({
                            'video_link': href,
                            'title': '',
                            'description': '',
                            'source_page': self.__driver.current_url,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        })

        return {
            'videos_from_iframes': video_data,
            'video_links_data': video_links_data
        }