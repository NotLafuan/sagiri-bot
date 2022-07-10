import discord
import requests
import html
from dataclasses import dataclass
from typing import Optional


@dataclass
class Title:
    _romaji: str
    _english: str
    _native: str
    _preferred: str

    @property
    def romaji(self) -> str:
        return self._romaji if self._romaji else ''

    @property
    def english(self) -> str:
        return self._english if self._english else ''

    @property
    def native(self) -> str:
        return self._native if self._native else ''

    @property
    def preferred(self) -> str:
        return self._preferred if self._preferred else ''


@dataclass
class Name:
    _full: str
    _native: str
    _preferred: str

    @property
    def full(self) -> str:
        return self._full if self._full else ''

    @property
    def native(self) -> str:
        return self._native if self._native else ''

    @property
    def preferred(self) -> str:
        return self._preferred if self._preferred else ''


@dataclass
class MediaInfo:
    type: str
    url: str
    id: int
    _color: str
    title: Title
    _description: str
    format: str
    _status: str
    _source: str
    popularity: int
    is_adult: bool

    @property
    def image(self) -> str:
        return f'https://img.anili.st/media/{self.id}'

    @property
    def color(self) -> discord.Color:
        if self._color:
            return discord.Color.from_rgb(
                *hex_to_rgb(self._color)
            )
        else:
            return None

    @property
    def description(self) -> str:
        if not self._description:
            return ''
        # description formatting (spoilers, italics, etc.)
        description: str = (html.unescape(self._description)
                            .replace('~!', '||')
                            .replace('!~', '||')
                            .replace('<i>', '*')
                            .replace('</i>', '*')
                            .replace('<br>', '')
                            .replace('__', '**'))
        # char limit
        limit = 350
        if len(description) > limit:
            if (description[:limit-3].count('||') % 2) == 0:
                return description[:limit-3] + '...'
            else:
                return description[:limit-3] + '...||'
        else:
            return description

    @property
    def status(self) -> str:
        return self._status.replace('_', ' ').title() if self._status else '`null`'

    @property
    def source(self) -> str:
        return self._source.replace('_', ' ').title() if self._source else '`null`'

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title.romaji,
            description=f'{self.title.english}\n{self.title.native}\n\n{self.description}',
            url=self.url,
            color=self.color
        )
        embed.add_field(name='Format', value=self.format)
        # if self.type == 'ANIME':
        #     embed.add_field(name='Episodes', value=self.episodes)
        # elif self.type == 'MANGA':
        #     embed.add_field(name='Chapters', value=self.chapters)
        embed.add_field(name='Status', value=self.status)
        # embed.add_field(name='Average Score',
        #                 value=self.averageScore)
        # embed.add_field(name='Genres', value=self.genres)
        embed.add_field(name='Source', value=self.source)
        embed.set_image(url=self.image)
        return embed


@dataclass
class CharacterInfo:
    url: str
    image: str
    name: Name
    _description: str
    _gender: str
    _age: str
    dateOfBirth: dict
    media: MediaInfo
    popularity: int

    @property
    def description(self) -> str:
        if not self._description:
            return ''
        # description formatting (spoilers, italics, etc.)
        description: str = (self._description
                            .replace('~!', '||')
                            .replace('!~', '||')
                            .replace('<i>', '*')
                            .replace('</i>', '*')
                            .replace('<br>', '')
                            .replace('__', '**'))
        # char limit
        limit = 350
        if len(description) > limit:
            if (description[:limit-3].count('||') % 2) == 0:
                return description[:limit-3] + '...'
            else:
                return description[:limit-3] + '...||'
        else:
            return description

    @property
    def gender(self) -> str:
        gender_dict = {'Female': '♀️', 'Male': '♂️', None: '`null`'}
        return gender_dict[self._gender]

    @property
    def birthday(self) -> str:
        month_dict = {1: 'Jan',
                      2: 'Feb',
                      3: 'Mar',
                      4: 'Apr',
                      5: 'May',
                      6: 'Jun',
                      7: 'Jul',
                      8: 'Aug',
                      9: 'Sep',
                      10: 'Oct',
                      11: 'Nov',
                      12: 'Dec'}
        if self.dateOfBirth['day']:
            birthday: str = f'{self.dateOfBirth["day"]} {month_dict[self.dateOfBirth["month"]]}'
            if self.dateOfBirth['year']:
                birthday += f' {self.dateOfBirth["year"]}'
        else:
            birthday = '`null`'
        return birthday

    @property
    def age(self) -> str:
        return self._age if self._age else '`null`'

    @property
    def origin(self) -> str:
        return f'[{self.media.title.preferred}]({self.media.url}) `[{self.media.format.replace("_", " ")}]`'

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.name.full,
                              description=f'{self.name.native}\n\n{self.description}',
                              url=self.url,
                              color=self.media.color)
        embed.add_field(name='Gender', value=self.gender)
        embed.add_field(name='Age',
                        value=self.age if self.age else '`null`')
        embed.add_field(name='Birthday', value=self.birthday)
        embed.add_field(name='From',
                        value=self.origin)
        embed.set_image(url=self.image)
        return embed


def hex_to_rgb(hex: str) -> tuple[int, int, int]:
    hex = hex.lstrip('#')
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))


def make_requests(query: str, variables: dict) -> Optional[dict]:
    endpoint = 'https://graphql.anilist.co'
    r = requests.post(endpoint, json={
        'variables': variables,
        'query': query,
    })
    if r.status_code == 200:
        if 'errors' not in r.json():
            return r.json()['data']


def get_media_info(result: dict) -> MediaInfo:
    if not result:
        return None
    media = result['Media']
    title = Title(
        media['title']['romaji'],
        media['title']['english'],
        media['title']['native'],
        media['title']['userPreferred'],
    )
    info = MediaInfo(
        media['type'],
        media['siteUrl'],
        media['id'],
        media['coverImage']['color'],
        title,
        media['description'],
        media['format'],
        media['status'],
        media['source'],
        media['popularity'],
        media['isAdult']
    )
    return info


def get_character_info(result: dict) -> CharacterInfo:
    if not result:
        return None
    character = result['Character']
    name = Name(
        character['name']['full'],
        character['name']['native'],
        character['name']['userPreferred']
    )
    top_media = max(
        character['media']['nodes'],
        key=lambda x: x['popularity'] if x['popularity'] else 0
    )
    info = CharacterInfo(
        character['siteUrl'],
        character['image']['large'],
        name,
        character['description'],
        character['gender'],
        character['age'],
        character['dateOfBirth'],
        get_animanga_from_id(top_media['id']),
        top_media['popularity']
    )
    return info


def get_animanga(search: str, is_adult: bool = False) -> MediaInfo:
    query = ('query($search:String,$is_adult:Boolean){Media(search:$search,'
             'isAdult:$is_adult){id type siteUrl coverImage{extraLarge colo'
             'r}title{romaji english native userPreferred}description forma'
             't status source popularity isAdult}}')
    variables = {
        'search': search,
        'is_adult': is_adult,
    }
    result = make_requests(query, variables)
    return get_media_info(result)


def get_animanga_from_id(id: int) -> MediaInfo:
    query = ('query($id:Int){Media(id:$id){id type siteUrl coverImage{extra'
             'Large color}title{romaji english native userPreferred}descrip'
             'tion format status source popularity isAdult}}')
    variables = {
        'id': id,
    }
    result = make_requests(query, variables)
    return get_media_info(result)


def get_anime(search: str, is_adult: bool = False) -> MediaInfo:
    query = ('query($search:String,$is_adult:Boolean){Media(search:$search,'
             'type:ANIME,isAdult:$is_adult){id type siteUrl coverImage{extr'
             'aLarge color}title{romaji english native userPreferred}descri'
             'ption format status source popularity isAdult}}')

    variables = {
        'search': search,
        'is_adult': is_adult,
    }
    result = make_requests(query, variables)
    return get_media_info(result)


def get_manga(search: str, is_adult: bool = False) -> MediaInfo:
    query = ('query($search:String,$is_adult:Boolean){Media(search:$search,'
             'type:MANGA,isAdult:$is_adult){id type siteUrl coverImage{extr'
             'aLarge color}title{romaji english native userPreferred}descri'
             'ption format status source popularity isAdult}}')
    variables = {
        'search': search,
        'is_adult': is_adult,
    }
    result = make_requests(query, variables)
    return get_media_info(result)


def get_character(search: str) -> CharacterInfo:
    query = ('query($search:String){Character(search:$search){siteUrl image'
             '{large medium}name{first middle last full native userPreferre'
             'd}description gender age dateOfBirth{year month day}media{nod'
             'es{popularity id}}}}')
    variables = {
        'search': search,
    }
    result = make_requests(query, variables)
    return get_character_info(result)
