#!/usr/bin/python

import datetime
import functools
import pytz

from .enums import *
from .utils import *


@functools.total_ordering
class DateTimeInterval:
    def __init__(self, entity):
        self.duration = getEntity(entity, 'espi:duration',
                                  lambda e: datetime.timedelta(seconds=int(e.text)))
        self.start = getEntity(entity, 'espi:start',
                               lambda e: datetime.datetime.fromtimestamp(int(e.text), pytz.timezone("UTC")))
        
    def __repr__(self):
        return '<DateTimeInterval (%s, %s)>' % (self.start, self.duration)

    def __eq__(self, other):
        if not isinstance(other, DateTimeInterval):
            return False
        return (self.start, self.duration) == (other.start, other.duration)
    
    def __lt__(self, other):
        if not isinstance(other, DateTimeInterval):
            return False
        return (self.start, self.duration) < (other.start, other.duration)

    
@functools.total_ordering
class IntervalReading:
    def __init__(self, entity, parent):
        self.intervalBlock = parent
        self.cost = getEntity(entity, 'espi:cost', lambda e: int(e.text) / 100000.0)
        self.timePeriod = getEntity(entity, 'espi:timePeriod',
                                    lambda e: DateTimeInterval(e))
        self._value = getEntity(entity, 'espi:value', lambda e: int(e.text))

        self.tou = getEntity(entity, 'espi:tou', lambda e: int(e.text))

        self.readingQualities = set([ReadingQuality(rq, self) for rq in entity.findall('espi:ReadingQuality', ns)])
        
    def __repr__(self):
        return '<IntervalReading (%s, %s: %s %s)>' % (self.timePeriod.start, self.timePeriod.duration, self.value, self.value_symbol)

    def __eq__(self, other):
        if not isinstance(other, IntervalReading):
            return False
        return (self.timePeriod, self.value) == (other.timePeriod, other.value)
    
    def __lt__(self, other):
        if not isinstance(other, IntervalReading):
            return False
        return (self.timePeriod, self.value) < (other.timePeriod, other.value)
    
    @property
    def value(self):
        if self.intervalBlock is not None and \
           self.intervalBlock.meterReading is not None and \
           self.intervalBlock.meterReading.readingType is not None and \
           self.intervalBlock.meterReading.readingType.powerOfTenMultiplier is not None:
            multiplier = 10 ** self.intervalBlock.meterReading.readingType.powerOfTenMultiplier
        else:
            multiplier = 1
        return self._value * multiplier

    @property
    def cost_units(self):
        if self.intervalBlock is not None and \
           self.intervalBlock.meterReading is not None and \
           self.intervalBlock.meterReading.readingType is not None and \
           self.intervalBlock.meterReading.readingType.currency is not None:
            return self.intervalBlock.meterReading.readingType.currency
        else:
            return CurrencyCode.na

    @property
    def cost_symbol(self):
        return self.cost_units.symbol

    @property
    def cost_uom_id(self):
        return self.cost_units.uom_id

    @property
    def value_units(self):
        if self.intervalBlock is not None and \
           self.intervalBlock.meterReading is not None and \
           self.intervalBlock.meterReading.readingType is not None and \
           self.intervalBlock.meterReading.readingType.uom is not None:
            return self.intervalBlock.meterReading.readingType.uom
        else:
            return UomType.notApplicable

    @property
    def value_symbol(self):
        return UOM_SYMBOLS[self.value_units]

    @property
    def value_uom_id(self):
        if self.value_units in UOM_IDS:
            return UOM_IDS[self.value_units]
        else:
            return None
        
class ReadingQuality:
    def __init__(self, entity, parent):
        self.intervalReading = parent
        self.quality = getEntity(entity, 'espi:quality', lambda e: QualityOfReading(int(e.text)))
