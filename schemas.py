from pydantic import BaseModel
from datetime import datetime


class DownloadParameters(BaseModel):
    start_date: datetime
    end_date: datetime
    account_name: str
    account_number: str
    account_phone: str

class DatabaseRecord(BaseModel):
    interval_start: datetime
    usage: float
    cost: float
    tou: int

class DatabaseConfig(BaseModel):
    database: str
    user: str
    password: str
    host: str

class AlectraCredentials(BaseModel):
    account_name: str
    account_number: str
    account_phone: str