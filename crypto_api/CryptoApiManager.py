import aiohttp
import grequests
from typing_extensions import Union

import config
from services.deposit import DepositService


class CryptoApiManager:
    def __init__(self, ltc_address, user_id):
        self.ltc_address = ltc_address.strip()
        self.user_id = user_id

    @staticmethod
    async def fetch_api_request(url: str, params: Union[dict, None] = None) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data

    async def get_ltc_balance(self, deposits) -> float:
        url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{self.ltc_address}?unspentOnly=true"
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if deposit.network == "LTC"]
        deposits_sum = 0.0
        if data['n_tx'] > 0:
            for deposit in data['txrefs']:
                if deposit["confirmations"] > 0 and deposit['tx_hash'] not in deposits:
                    await DepositService.create(deposit['tx_hash'], self.user_id, "LTC",
                                                deposit["value"], deposit['tx_output_n'])
                    deposits_sum += float(deposit['value']) / 100_000_000
        return deposits_sum

    async def get_top_up_by_crypto_name(self, crypto_name: str):
        user_deposits = await DepositService.get_by_user_id(self.user_id)

        crypto_functions = {
            "LTC": ("ltc_deposit", self.get_ltc_balance),
        }

        if "_" in crypto_name:
            base, token = crypto_name.split('_')
        else:
            base, token = crypto_name, None

        key = f"{base}_{token}" if token else base
        deposit_name, balance_func = crypto_functions.get(key, (None, None))

        if deposit_name and balance_func:
            return {deposit_name: await balance_func(user_deposits)}
        raise ValueError(f"Unsupported crypto name: {crypto_name}")

    @staticmethod
    async def get_usd_to_ron_rate() -> float:
        url = "https://api.getgeoapi.com/v2/currency/convert"
        params = {"api_key": config.GETGEOAPI_KEY,
                  "from": "USD",
                  "to": "RON",
                  "amount": 1,
                  "format": "json"}
        response = await CryptoApiManager.fetch_api_request(url, params)
        return float(response['rates']['RON']['rate'])

    @staticmethod
    async def get_crypto_prices() -> dict[str, float]:
        usd_crypto_prices = {}
        urls = {
            "ltc": f'https://api.kraken.com/0/public/Ticker?pair=LTCUSD',
        }
        responses = (grequests.get(url) for url in urls.values())
        datas = grequests.map(responses)
        usd_to_ron_rate = await CryptoApiManager.get_usd_to_ron_rate()
        for symbol, data in zip(urls.keys(), datas):
            data = data.json()
            price = float(next(iter(data['result'].values()))['c'][0])
            usd_crypto_prices[symbol] = price*usd_to_ron_rate
        return usd_crypto_prices
