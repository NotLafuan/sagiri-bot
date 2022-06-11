import discord
from discord.ext import commands
from dataclasses import dataclass, field
import json
from datetime import timedelta, datetime
import numpy as np
import os
import subprocess
from typing import Literal, Mapping, Optional

# spotify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# .env
from dotenv import load_dotenv, find_dotenv
import yt_dlp
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
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

ERROR = 'error'
WARNING = 'warning'
MESSAGE = 'message'

SILVER: discord.Color = discord.Color.from_rgb(r=203, g=213, b=225)

EMPTY_CHAR = '‎'


class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], list[commands.Command]]):
        embed = discord.Embed(color=SILVER)
        embed.set_author(
            name='Help Command',
            icon_url=self.context.bot.user.avatar_url
        )
        for cog, _commands in mapping.items():
            if cog and cog.qualified_name != 'database':
                name = f'{cog.qualified_name} commands'.capitalize()
                value = ', '.join(
                    [f'`{command.name}`' for command in _commands]
                )
                embed.add_field(name=name, value=value, inline=False)
        embed.set_footer(
            text=f'Type \'{self.clean_prefix}help <CommandName>\' for details on a command'
        )
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        name = f'{cog.qualified_name} commands'.capitalize()
        value = ', '.join(
            [f'`{command.name}`' for command in cog.get_commands()]
        )

        embed = discord.Embed(color=SILVER)
        embed.set_author(
            name='Category',
            icon_url=self.context.bot.user.avatar_url
        )
        embed.add_field(name=name, value=value, inline=False)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(
            color=SILVER,
            description='Aliases: ' +
            ', '.join([f'`{alias}`' for alias in group.aliases]
                      ) if group.aliases else discord.Embed.Empty
        )
        embed.set_author(
            name=f'Help Command: {group.name}',
            icon_url=self.context.bot.user.avatar_url
        )
        arguments = group.help.split('|')
        descriptions = group.description.split('|')
        for argument, description in zip(arguments, descriptions):
            embed.add_field(
                name=f'{self.clean_prefix}{group.name} {argument}',
                value=f'{description}\n{EMPTY_CHAR}',
                inline=False
            )

        _commands: list[commands.Command] = list(group.commands)
        for command in _commands:
            arguments = command.help.split('|')
            descriptions = command.description.split('|')
            if command != _commands[-1]:
                for argument, description in zip(arguments, descriptions):
                    embed.add_field(
                        name=f'{self.clean_prefix}{group.name} {command.name} {argument}',
                        value=f'{description}\n{EMPTY_CHAR}',
                        inline=False
                    )
            else:
                for argument, description in zip(arguments, descriptions):
                    embed.add_field(
                        name=f'{self.clean_prefix}{group.name} {command.name} {argument}',
                        value=f'{description}',
                        inline=False
                    )
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            color=SILVER,
            description='Aliases: ' +
            ', '.join([f'`{alias}`' for alias in command.aliases]
                      ) if command.aliases else discord.Embed.Empty
        )
        embed.set_author(
            name=f'Help Command: {command.name}',
            icon_url=self.context.bot.user.avatar_url
        )
        arguments = command.help.split('|')
        descriptions = command.description.split('|')
        for argument, description in zip(arguments, descriptions):
            if argument != arguments[-1]:
                embed.add_field(
                    name=f'{self.clean_prefix}{command.name} {argument}',
                    value=f'{description}\n{EMPTY_CHAR}',
                    inline=False
                )
            else:
                embed.add_field(
                    name=f'{self.clean_prefix}{command.name} {argument}',
                    value=f'{description}',
                    inline=False
                )
        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: str):
        error = error.replace('"', '`')
        embed = discord.Embed(description=error, color=discord.Color.red())
        msg: discord.Message = await self.get_destination().send(embed=embed)
        await msg.delete(delay=3)


def get_prefix(client: commands.Bot, message: discord.Message):
    return client.server_info[message.guild.id].prefix


def load_info(client: commands.Bot, filename: str = 'server_info.json'):
    with open(filename, 'r') as f:
        server_info = json.load(f)

    for guild in client.guilds:
        if str(guild.id) in server_info:
            properties = server_info[str(guild.id)]
            client.server_info[guild.id] = ServerInfo(**properties)
        else:
            client.server_info[guild.id] = ServerInfo('.', 100., 'off')

    save_info(client)


def save_info(client: commands.Bot, filename: str = 'server_info.json'):
    save_dict: dict = {}

    for guild in client.server_info:
        save_dict[guild] = {
            'prefix': client.server_info[guild].prefix,
            'volume': client.server_info[guild].volume,
            'loop': client.server_info[guild].loop,
        }

    with open(filename, 'w+') as f:
        json.dump(save_dict, f, indent=4, ensure_ascii=False)


def add_info(client: commands.Bot, guild: discord.Guild):
    client.server_info[guild.id] = ServerInfo('.', 100., 'off')


def remove_info(client: commands.Bot, guild: discord.Guild):
    client.server_info.pop(guild.id)


async def send_notice(ctx: commands.Context, message: str, notice_type: str = ERROR, delay: int | None = None) -> discord.Message:
    if notice_type == ERROR:
        color = discord.Color.red()
    elif notice_type == WARNING:
        color = discord.Color.gold()
    elif notice_type == MESSAGE:
        color = SILVER
    embed = discord.Embed(
        description=message,
        color=color
    )
    notice: discord.Message = await ctx.send(embed=embed)
    if delay:
        await notice.delete(delay=delay)
    return notice


@dataclass
class ServerInfo():
    prefix: str
    volume: float
    loop: str


@dataclass(eq=True, order=True)
class Time:
    value: float

    def __str__(self):
        time_str = str(timedelta(seconds=int(self.value)))
        time_str = time_str.split(':')  # split hours, minutes, seconds
        time_str = [x for x in time_str if x != '0']  # remove if hours is 0
        time_str = ':'.join(time_str)  # stitch back together
        return time_str

    def __float__(self):
        return self.value

    def __int__(self):
        return int(self.value)

    def __add__(self, other):
        return Time(self.value + other.value)

    def __sub__(self, other):
        return Time(self.value - other.value)

    def __mul__(self, other):
        return Time(self.value * other.value)

    def __truediv__(self, other):
        return Time(self.value / other.value)

    def __floordiv__(self, other):
        return Time(self.value // other.value)

    def __pow__(self, other):
        return Time(self.value ** other.value)


@dataclass
class Song():
    """Represents a Song.

    Attributes
    -----------
    type: :class:`str`
        The song origin, eg. spotify, youtube.
    title: :class:`str`
        The song title.
    thumbnail: :class:`str`
        The thumbnail url.
    duration: :class:`Time`
        The song's duration.
    yturl: :class:`str`
        The url from youtube.
    spurl: :class:`str`
        The url from spotify.
    url: :class:`str`
        The song's audio file url.
    source: :class:`discord.FFmpegPCMAudio`
        The source for playing the song.
    start_time: :class:`datetime`
        Store when the song start playing.
    delta: :class:`float`
        To track the song's progress.
    """
    type: str
    title: str
    thumbnail: str
    duration: Time
    yturl: str | None = None
    spurl: str | None = None
    url: str | None = None
    source: discord.FFmpegPCMAudio | None = None
    start_time: datetime = datetime.now()
    delta: float = 0.

    def reset_time(self):
        self.start_time = datetime.now()

    def save_progress(self):
        delta = datetime.now() - self.start_time
        self.delta = delta.total_seconds()

    def set_progress(self, seconds: float):
        self.delta = seconds

    def set_progress_str(self, timestr: str):
        ftr = [1, 60, 3600]
        timelist = timestr.split(':')
        timelist.reverse()
        seconds = sum([a * b for a, b in zip(ftr, map(int, timelist))])
        self.delta = seconds

    @property
    def progress_bar(self, width: int = 17, fill: str = '▬', url: str = 'https://anilist.co/character/89576/Sagiri-Izumi'):
        progress = float(self.progress/self.duration)
        # 0 <= progress <= 1
        progress = min(1, max(0, progress))
        whole_width = int(np.round(progress * width))
        remainder_width = width - whole_width
        bar = fill * whole_width
        bar = f'[{bar}]({url})'
        bar += fill * remainder_width
        return bar

    @property
    def progress_str(self) -> str:
        return f'{self.progress}/{self.duration}'

    @property
    def progress(self) -> Time:
        delta = datetime.now() - self.start_time
        delta = delta.total_seconds() + self.delta
        return Time(delta)

    @property
    def links(self):
        if self.type == 'file':
            links = f'[Url]({self.url})'
        else:
            links = []
            if self.yturl:
                links.append(f'[YouTube]({self.yturl})')
            if self.spurl:
                links.append(f'[Spotify]({self.spurl})')
            links = ' | '.join(links)
        return links if links else discord.Embed.Empty

    @property
    def link(self) -> str:
        if self.yturl:
            return self.yturl
        elif self.spurl:
            return self.spurl
        else:
            return self.url

    def extract_url(self):
        if self.url:
            pass
        elif self.type == 'file':
            pass
        elif self.type == 'spotify':
            data = ytdl.extract_info(self.title, download=False, process=True)
            self.yturl = data['entries'][0]['webpage_url']
            self.url = data['entries'][0]['url']
        elif self.type == 'youtube':
            data = ytdl.extract_info(self.yturl, download=False, process=False)
            self.url = data['formats'][-1]['url']

    def extract_source(self) -> discord.FFmpegPCMAudio:
        if self.source:
            source = self.source
            self.source = None
        else:
            if not self.url:
                self.extract_url()
            source = discord.FFmpegPCMAudio(self.url, **FFMPEG_OPTIONS)
        return source


@dataclass
class ServerMusic():
    """Container for managing music in a server.

    Attributes
    -----------
    queue: List[:class:`Song`]
        The song queue.
    vc: :class:`discord.VoiceClient`
        The voice client of the server.
    is_playing: :class:`bool`
        Playing status.
    current_song: :class:`Song`
        The currently playing song.
    queue_msg: Dict[:class:`int`,:class:`discord.Message`]
        The queue messages in the server.
    now_playing: :class:`discord.Message`
        The now playing message.
    """
    queue: list[Song] = field(default_factory=list)
    vc: discord.VoiceClient = None
    is_playing: bool = False
    current_song: Song | None = None
    queue_msg: dict[int, discord.Message] = field(default_factory=dict)
    now_playing: discord.Message = None

    def __len__(self):
        return len(self.queue)

    def clear(self):
        self.queue.clear()

    def shuffle(self):
        np.random.shuffle(self.queue)

    def remove(self, pos: int):
        del self.queue[pos]

    def move(self, _from: int, _to: int):
        self.queue.insert(_to, self.queue.pop(_from))

    def swap(self, pos1: int, pos2: int):
        self.queue[pos1], self.queue[pos2] = self.queue[pos2], self.queue[pos1]

    def reverse(self):
        self.queue.reverse()


@dataclass
class Playlist():
    title: str
    url: str
    thumbnail: str
    duration: Time
    track_num: int


class Youtube():
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
        except:
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
        except:
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
                url=entry['formats'][-1]['url']
            )
            return song
        except:
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
        except:
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
        except:
            return False

    def search_url(self, link: str) -> Song:
        filename, fileext = os.path.splitext(link)
        if fileext in self.FILE_EXTS:
            filename = filename.split('/')[-1]
            sec = self.sec_from_url(link)
            if sec:
                song = Song(
                    type='file',
                    title=f'{fileext[1:]} - {filename}',
                    thumbnail=None,
                    duration=Time(int(sec)),
                    url=link,
                )
                return song
            else:
                raise Exception('Unable to play this file.')
        else:
            raise Exception(
                'Invalid File type provided!\nSupported formats are: `wav, matroska/webm, mp4, flac, ogg, mp3`'
            )


def search(query: str) -> tuple[list[Song], Playlist | Literal[False]]:
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
