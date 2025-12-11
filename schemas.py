from pydantic import BaseModel, DirectoryPath
from datetime import datetime


class DownloadParameters(BaseModel):
    start_date: datetime
    end_date: datetime
    output_dir: DirectoryPath
    account_name: str
    account_number: str
    account_phone: str

class DatabaseRecord(BaseModel):
    timestamp: datetime
    value_kwh: float
    cost: float
    tou: int