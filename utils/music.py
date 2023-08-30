import discord
from discord.ui import View, Button
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta

SILVER: discord.Color = discord.Color.from_rgb(r=203, g=213, b=225)


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
class Playlist:
    title: str
    url: str
    thumbnail: str
    duration: Time
    track_num: int


@dataclass
class Song:
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
        return links if links else None

    @property
    def link(self) -> str:
        if self.yturl:
            return self.yturl
        elif self.spurl:
            return self.spurl
        else:
            return self.url

    def extract_url(self):
        from .search import ytdl, Youtube
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
            self.url = Youtube.get_url_from_formats(data['formats'])

    def extract_source(self) -> discord.FFmpegPCMAudio:
        from .search import FFMPEG_OPTIONS
        if self.source:
            source = self.source
            self.source = None
        else:
            if not self.url:
                self.extract_url()
            source = discord.FFmpegPCMAudio(self.url, **FFMPEG_OPTIONS)
        return source


@dataclass
class ServerMusic:
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


class QueueEmbed:
    def __init__(self,
                 server_music: ServerMusic,
                 page: int,
                 per_page: int = 10) -> None:
        self.view: View = self.create_view()
        self.server_music = server_music
        self.page = page
        self.per_page = per_page

    def add(self, add: int):
        self.page += add

    def set(self, value: int):
        self.page = value

    def create_view(self) -> View:
        button_first = Button(label='<<')
        button_backward = Button(label='<')
        button_forward = Button(label='>')
        button_last = Button(label='>>')

        async def first_callback(interaction: discord.Interaction):
            self.set(10**10)
            await interaction.response.edit_message(embed=self.embed)

        async def backward_callback(interaction: discord.Interaction):
            self.add(-1)
            await interaction.response.edit_message(embed=self.embed)

        async def forward_callback(interaction: discord.Interaction):
            self.add(1)
            await interaction.response.edit_message(embed=self.embed)

        async def last_callback(interaction: discord.Interaction):
            self.set(0)
            await interaction.response.edit_message(embed=self.embed)

        button_first.callback = first_callback
        button_backward.callback = backward_callback
        button_forward.callback = forward_callback
        button_last.callback = last_callback
        view = View()
        view.add_item(button_first)
        view.add_item(button_backward)
        view.add_item(button_forward)
        view.add_item(button_last)
        return view

    @property
    def embed(self) -> discord.Embed:
        queue_len = len(self.server_music.queue)
        page_len = int(np.ceil(queue_len/self.per_page))
        # loop page
        self.page = page_len if self.page < 1 else self.page
        self.page = 1 if self.page > page_len else self.page
        # cut the queue
        lower_bound = (self.page - 1) * self.per_page
        upper_bound = (self.page) * self.per_page
        if self.page == page_len:  # last page
            songs = self.server_music.queue[lower_bound:]
        else:
            songs = self.server_music.queue[lower_bound:upper_bound]
        # generate text
        first_num = ((self.page - 1) * self.per_page) + 1
        text = ''
        for i, song in enumerate(songs):
            text += f'{first_num+i}. {song.title} [{song.duration}]\n'
        footer = f'Page {self.page}/{page_len}'
        embed = discord.Embed(description=text, color=SILVER)
        embed.set_footer(text=footer)
        return embed
