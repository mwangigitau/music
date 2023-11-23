from pydantic import BaseModel
from datetime import datetime


class RabbitMQ(BaseModel):
    Host: str
    Port: int
    Username: str
    Password: str


class Test(BaseModel):
    Name: str


class Configuration(BaseModel):
    TestCollection: Test
    RabbitMQ: RabbitMQ


class Message(BaseModel):
    SongURL: str


class DatabaseObject(BaseModel):
    SongName: str
    DateAdded: datetime
    Data: bytes
    Song: bytes
