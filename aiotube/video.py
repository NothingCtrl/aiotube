import re
import json
from .https import video_data
from typing import Dict, Any


class Video:

    _HEAD = 'https://www.youtube.com/watch?v='

    def __init__(self, video_id: str):
        """
        Represents a YouTube video

        Parameters
        ----------
        video_id : str
            The id or url of the video
        """
        try:
            pattern = re.compile('.be/(.*?)$|=(.*?)$|^(\w{11})$')  # noqa
            self._matched_id = (
                    pattern.search(video_id).group(1)
                    or pattern.search(video_id).group(2)
                    or pattern.search(video_id).group(3)
            )
        except AttributeError:
            # some video id is not match, example: 'UeqP-7eEgc8'
            self._matched_id = video_id
        if self._matched_id:
            self._url = self._HEAD + self._matched_id
            self._video_data = video_data(self._matched_id)
        else:
            raise ValueError('invalid video id or url')

    def __repr__(self):
        return f'<Video {self._url}>'

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Fetches video metadata in a dict format

        Returns
        -------
        Dict
            Video metadata in a dict format containing keys: title, id, views, duration, author_id,
            upload_date, url, thumbnails, tags, description
        """
        details_pattern = re.compile('videoDetails\":(.*?)\"isLiveContent\":.*?}')
        upload_date_pattern = re.compile("<meta itemprop=\"uploadDate\" content=\"(.*?)\">")
        genre_pattern = re.compile("<meta itemprop=\"genre\" content=\"(.*?)\">")
        like_count_pattern = re.compile("iconType\":\"LIKE\"},\"defaultText\":(.*?)}}")
        groups = details_pattern.search(self._video_data)
        if not groups:
            groups = re.compile('videoDetails\":(.*?)\"autonavToggle\":.*?}').search(self._video_data)
        raw_details = groups.group(0)
        if ',"autonavToggle":' in raw_details:
            raw_details = raw_details.split(',"autonavToggle":')[0]
        metadata = json.loads(raw_details.replace('videoDetails\":', ''))
        if "title" not in metadata:
            return {}
        data = {
            'title': metadata['title'],
            'id': metadata['videoId'],
            'views': metadata.get('viewCount'),
            'streamed': metadata['isLiveContent'],
            'duration': metadata['lengthSeconds'],
            'author_id': metadata['channelId'],
            'upload_date': None,
            'url': f"https://www.youtube.com/watch?v={metadata['videoId']}",
            'thumbnails': metadata.get('thumbnail', {}).get('thumbnails'),
            'tags': metadata.get('keywords'),
            'description': metadata.get('shortDescription'),
            'likes': None,
            'genre': None
        }
        try:
            likes_count = like_count_pattern.search(self._video_data).group(1)
            data['likes'] = json.loads(likes_count + '}}}')[
                'accessibility'
            ]['accessibilityData']['label'].split(' ')[0].replace(',', '')
        except (AttributeError, KeyError, json.decoder.JSONDecodeError):
            pass
        try:
            data['genre'] = genre_pattern.search(self._video_data).group(1)
        except AttributeError:
            pass
        try:
            data['upload_date'] = upload_date_pattern.search(self._video_data).group(1)
        except AttributeError:
            pass
        return data
