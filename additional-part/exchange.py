import sys
import asyncio
from datetime import datetime, timedelta
from aiohttp import ClientSession


API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
MAX_DAYS = 10
CURRENCY_LIST = ["EUR", "USD"]


async def pars_url(day:int) -> str:
    pars_date = (datetime.now().date() - timedelta(days=day)).strftime('%d.%m.%Y')
    return f"{API_URL}{pars_date}"


async def pars_data(data:dict, currencies:list) -> dict:
    rezult = {data["date"]: {}}
    for exchange_rate in data["exchangeRate"]:
        if exchange_rate["currency"] in currencies:
            
            rezult[data["date"]].update(
                {exchange_rate["currency"]: {
                    "sale": exchange_rate["saleRate"],
                    "purchase" : exchange_rate["purchaseRate"]
                    }})
    return rezult


async def json_get(day:int, session: ClientSession) -> dict:
    url = await pars_url(day)

    async with session.get(url) as response:
        status = response.status
        
        if status == 200:
            data = await response.json()

    return data


async def create_session(last_day:int, currencies:list) -> list:
    async with ClientSession() as session:
        rezult = await asyncio.gather(*[json_get(day, session) for day in range(last_day)])
    return [await pars_data(el, currencies) for el in rezult]


async def main():
    last_day = sys.argv[1] if len(sys.argv) > 1 else "1"
    add_currencies = sys.argv[2:]

    if not last_day.isdecimal():
        raise ValueError(f"Type '{last_day}' is not integer.")

    if not (0 < int(last_day) <= MAX_DAYS):
        raise ValueError(f"The maximum number of days should not exceed {MAX_DAYS}.")
    
    currencies = [el.upper() for el in [*CURRENCY_LIST, *add_currencies]]
    currencies.sort()
    
    rezult = await create_session(int(last_day), currencies)

    [print(r) for r in rezult]
    

if __name__ == "__main__":
    
    try:
        asyncio.run(main())
    except ValueError as error:
        print(error.args[0])
    