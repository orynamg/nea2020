from dataclasses import dataclass, field
from typing import Set, Union
from datetime import datetime

@dataclass
class Event:
    id: Union[int, None] = None
    name: str = ""
    summary: str = ""
    keywords: Set[str] = field(default_factory=set)
    created_at: datetime = datetime.utcnow()

@dataclass
class Tweet:
    id: Union[int, None] = None
    text: str = ""
    hashtags: str = ""
    url: str = ""
    user: str = ""
    category_id: Union[int, None] = None
    event_id: Union[int, None] = None
    published_at: datetime = datetime.utcnow()
    created_at: datetime = datetime.utcnow()


@dataclass
class News:
    id: Union[int, None] = None
    headline: str = ""
    source: str = ""
    url: str = ""
    image_url: str = ""
    country_code: str = ""
    category_id: Union[int, None] = None
    event_id: Union[int, None] = None
    text: str = ""
    summary: str = ""
    published_at: datetime = datetime.utcnow()
    created_at: datetime = datetime.utcnow()

