from pydantic import BaseModel
from datetime import datetime


class DownloadParameters(BaseModel):
    start_date: datetime
    end_date: datetime
    account_name: str
    account_number: str
    account_phone: str

class DatabaseRecord(BaseModel):
    timestamp: datetime
    value_kwh: float
    cost: float
    tou: int