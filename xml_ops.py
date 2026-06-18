from greenbutton import parse
from schemas import DatabaseRecord


def extract_interval_readings(xml_file) -> list:
    usagePoint = parse.parse_feed(xml_file)[0]
    meterReadings = usagePoint.meterReadings

    def get_correct_meter_reading(meter_readings):
        for meterReading in meter_readings:
            if meterReading.readingType and meterReading.readingType.title == 'KWH Interval Data':
                return meterReading
        raise Exception("KWH Interval Data meter reading not found")

    meterReading = get_correct_meter_reading(meterReadings)
    intervalBlocks = meterReading.intervalBlocks

    interval_readings = []
    for intervalBlock in intervalBlocks:
        for intervalReading in intervalBlock.intervalReadings:
            interval_readings.append(intervalReading)

    return interval_readings

def convert_to_database_records(interval_readings: list) -> list[DatabaseRecord]:
    records = []
    for intervalReading in interval_readings:
        record = DatabaseRecord(
            interval_start=intervalReading.timePeriod.start,
            usage=intervalReading.value / 1000.0,  # Convert Wh to kWh
            cost=intervalReading.cost,
            tou=intervalReading.tou
        )
        records.append(record)
    return records