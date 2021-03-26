from numpy import DataSource
from indicator import Indicator
from datetime import datetime

start = datetime.now()
print('Start time: ', start)
stock = Indicator('KASET')
result = stock.ema()
print(type(result))
print(result)
end = datetime.now()
print('End time: ', end)
print('Usage time: ', end - start)