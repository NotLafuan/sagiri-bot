import subprocess
import os
import yt_dlp
from .music import Song, Playlist, Time
from typing import Literal


# spotify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# .env
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'default_search': 'ytsearch',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0',
    'cookiefile': '/home/ubuntu/sagiri-bot/cookies.txt',
    'cookies': '/home/ubuntu/sagiri-bot/cookies.txt',
#    'cookiesfrombrowser': ('firefox', 'default', None, 'Meta'),
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class Youtube():
    def get_url_from_formats(self, formats) -> str | None:
        for format in reversed(formats):
            if 'manifest_url' in format or 'ext' not in format:
                continue
            elif format['ext'] == 'm4a':
                return format['url']

    def from_query(self, query: str) -> Song | Literal[False]:
        try:
            data = ytdl.extract_info(query, download=False, process=True)
            entry = data['entries'][0]
            song = Song(
                type='youtube',
                title=entry['title'],
                thumbnail=entry['thumbnail'],
                duration=Time(entry['duration']),
                yturl=entry['webpage_url'],
                url=entry['url']
            )
            return song
        except Exception:
            return False

    def from_query_multiple(self, query: str, amount: int = 5) -> list[Song] | Literal[False]:
        try:
            data = ytdl.extract_info(
                f'ytsearch{amount}:{query}',
                download=False,
                process=False
            )
            songs: list[Song] = []
            for entry in data['entries']:
                song = Song(
                    type='youtube',
                    title=entry['title'],
                    thumbnail=entry['thumbnails'][-1]['url'],
                    duration=Time(entry['duration']),
                    yturl=entry['url']
                )
                songs.append(song)
            return songs
        except Exception:
            return False

    def from_url(self, url: str) -> Song | Literal[False]:
        try:
            entry = ytdl.extract_info(url, download=False, process=False)
            song = Song(
                type='youtube',
                title=entry['title'],
                thumbnail=entry['thumbnail'],
                duration=Time(entry['duration']),
                yturl=entry['webpage_url'],
                url=self.get_url_from_formats(entry['formats'])
            )
            return song
        except Exception:
            return False

    def from_playlist(self, url: str) -> tuple[list[Song], Playlist] | Literal[False]:
        try:
            playlist_id = url.split('list=')[-1].split('&')[0]
            url = 'https://www.youtube.com/playlist?list=' + playlist_id
            data = ytdl.extract_info(url, download=False, process=False)
            songs: list[Song] = []
            track_num = 0
            duration = Time(0)
            for entry in data['entries']:
                track_num += 1
                duration += Time(entry['duration'])
                song = Song(
                    type='youtube',
                    title=entry['title'],
                    thumbnail=entry['thumbnails'][-1]['url'],
                    duration=Time(entry['duration']),
                    yturl=entry['url']
                )
                songs.append(song)
            playlist = Playlist(
                title=data['title'],
                url=data['webpage_url'],
                thumbnail=data['thumbnails'][-1]['url'],
                duration=duration,
                track_num=track_num
            )
            return songs, playlist
        except Exception:
            return False


class Spotify():
    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
    )

    def from_track(self, query: str) -> Song:
        result = self.sp.track(query)
        title = result['name']
        artist = result['artists'][0]['name'] if result['artists'] else None
        song = Song(
            type='spotify',
            title=f'{artist} - {title}' if artist else title,
            thumbnail=result['album']['images'][0]['url'] if result['album']['images'] else None,
            duration=Time(result['duration_ms']//1000),
            spurl=result['external_urls']['spotify'] if result['external_urls'] else None,
        )
        return song

    def from_playlist(self, query: str) -> tuple[list[Song], Playlist]:
        result = self.sp.playlist(query)
        # scroll through tracks pages
        tracks = result['tracks']['items']
        while result['tracks']['next']:
            result['tracks'] = self.sp.next(result['tracks'])
            tracks.extend(result['tracks']['items'])
        songs: list[Song] = []
        track_num = 0
        duration = Time(0)
        for track in tracks:
            track_num += 1
            duration += Time(track['track']['duration_ms']//1000)
            title = track['track']['name']
            artist = track['track']['artists'][0]['name'] if track['track']['artists'] else None
            song = Song(
                type='spotify',
                title=f'{artist} - {title}' if artist else title,
                thumbnail=track['track']['album']['images'][0]['url'] if track['track']['album']['images'] else None,
                duration=Time(track['track']['duration_ms']//1000),
                spurl=track['track']['external_urls']['spotify'] if track['track']['external_urls'] else None,
            )
            songs.append(song)
        playlist = Playlist(
            title=result['name'],
            url=result['external_urls']['spotify'],
            thumbnail=result['images'][0]['url'],
            duration=duration,
            track_num=track_num
        )
        return songs, playlist

    def from_album(self, query: str) -> tuple[list[Song], Playlist]:
        result = self.sp.album(query)
        # scroll through tracks pages
        tracks = result['tracks']['items']
        while result['tracks']['next']:
            result['tracks'] = self.sp.next(result['tracks'])
            tracks.extend(result['tracks']['items'])
        songs: list[Song] = []
        track_num = 0
        duration = Time(0)
        for track in tracks:
            track_num += 1
            duration += Time(track['duration_ms']//1000)
            title = track['name']
            artist = track['artists'][0]['name'] if track['artists'] else None
            song = Song(
                type='spotify',
                title=f'{artist} - {title}' if artist else title,
                thumbnail=result['images'][0]['url'] if result['images'] else None,
                duration=Time(track['duration_ms']//1000),
                spurl=track['external_urls']['spotify'] if track['external_urls'] else None,
            )
            songs.append(song)
        playlist = Playlist(
            title=result['name'],
            url=result['external_urls']['spotify'],
            thumbnail=result['images'][0]['url'],
            duration=duration,
            track_num=track_num
        )
        return songs, playlist


class File():
    FILE_EXTS = [
        '.wav',
        '.webm',
        '.mp4',
        '.flac',
        '.ogg',
        '.mp3'
    ]

    def sec_from_url(self, url: str) -> float | Literal[False]:
        try:
            cmd = f'ffprobe -i {url} -show_entries format=duration -v quiet -of csv="p=0"'
            output = subprocess.check_output(cmd, shell=True)
            return float(output)
        except Exception:
            return False

    def search_url(self, link: str) -> Song:
        filename, fileext = os.path.splitext(link)
        if fileext not in self.FILE_EXTS:
            raise Exception(
                'Invalid File type provided!\nSupported formats are: `wav, matroska/webm, mp4, flac, ogg, mp3`'
            )
        filename = filename.split('/')[-1]
        sec = self.sec_from_url(link)
        if not sec:
            raise Exception('Unable to play this file.')
        song = Song(
            type='file',
            title=f'{fileext[1:]} - {filename}',
            thumbnail=None,
            duration=Time(int(sec)),
            url=link,
        )
        return song


def search(query: str) -> tuple[list[Song], Playlist | Literal[False]]:
    """Auto song search."""
    youtube = Youtube()
    spotify = Spotify()
    file = File()
    songs: list[Song] = []
    playlist: Playlist | Literal[False] = False
    # spotify
    if query.startswith('https://open.spotify.com/track/') or query.startswith('spotify:track:'):
        songs.append(spotify.from_track(query))
    elif query.startswith('https://open.spotify.com/playlist/') or query.startswith('spotify:playlist:'):
        songs, playlist = spotify.from_playlist(query)
    elif query.startswith('https://open.spotify.com/album/') or query.startswith('spotify:album:'):
        songs, playlist = spotify.from_album(query)
    # youtube
    elif query.startswith('https://www.youtube.com/') or query.startswith('https://youtu.be/'):
        if 'playlist?list=' in query or '&list=' in query:
            songs, playlist = youtube.from_playlist(query)
        else:
            songs.append(youtube.from_url(query))
    # link
    elif query.startswith('https://'):
        songs.append(file.search_url(query))
    # query
    else:
        songs.append(youtube.from_query(query))
    songs = [song for song in songs if song]  # remove any failed song
    return songs, playlist
