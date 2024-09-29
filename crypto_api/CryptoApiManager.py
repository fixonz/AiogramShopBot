from datetime import datetime, timedelta

import aiohttp
import grequests

import config
from services.deposit import DepositService


class CryptoApiManager:
    def __init__(self, btc_address, ltc_address, trx_address, eth_address, user_id):
        self.btc_address = btc_address.strip()
        self.ltc_address = ltc_address.strip()
        self.trx_address = trx_address.strip()
        self.eth_address = eth_address.strip()
        self.user_id = user_id
        # self.min_timestamp = 0
        self.min_timestamp = int((datetime.now() - timedelta(hours=6)).timestamp()) * 1000

    @staticmethod
    async def fetch_api_request(url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data

    async def get_btc_balance(self, deposits) -> float:
        url = f'https://mempool.space/api/address/{self.btc_address}/utxo'
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if deposit.network == "BTC"]
        deposit_sum = 0.0
        for deposit in data:
            if deposit["txid"] not in deposits and deposit['status']['confirmed']:
                await DepositService.create(deposit['txid'], self.user_id, "BTC", None, deposit["value"])
                deposit_sum += float(deposit["value"]) / 100_000_000
        return deposit_sum

    async def get_ltc_balance(self, deposits) -> float:
        url = f"https://api.blockcypher.com/v1/ltc/main/addrs/{self.ltc_address}?unspendOnly=true"
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if deposit.network == "LTC"]
        deposits_sum = 0.0
        if data['n_tx'] > 0:
            for deposit in data['txrefs']:
                if deposit["confirmations"] > 0 and deposit['tx_hash'] not in deposits:
                    await DepositService.create(deposit['tx_hash'], self.user_id, "LTC", None, deposit["value"])
                    deposits_sum += float(deposit['value']) / 100_000_000
        return deposits_sum

    async def get_usdt_trc20_balance(self, deposits) -> float:
        url = f"https://api.trongrid.io/v1/accounts/{self.trx_address}/transactions/trc20?only_confirmed=true&min_timestamp={self.min_timestamp}&contract_address=TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t&only_to=true"
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if
                    deposit.network == "TRX" and deposit.token_name == "USDT_TRC20"]
        deposits_sum = 0.0
        for deposit in data['data']:
            if deposit['transaction_id'] not in deposits:
                await DepositService.create(deposit['transaction_id'], self.user_id, "TRX",
                                            "USDT_TRC20", deposit['value'])
                deposits_sum += float(deposit['value']) / pow(10, deposit['token_info']['decimals'])
        return deposits_sum

    async def get_usdd_trc20_balance(self, deposits) -> float:
        url = f"https://api.trongrid.io/v1/accounts/{self.trx_address}/transactions/trc20?only_confirmed=true&min_timestamp={self.min_timestamp}&contract_address=TPYmHEhy5n8TCEfYGqW2rPxsghSfzghPDn&only_to=true"
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if
                    deposit.network == "TRX" and deposit.token_name == "USDD_TRC20"]
        deposits_sum = 0.0
        for deposit in data['data']:
            if deposit['transaction_id'] not in deposits:
                await DepositService.create(deposit['transaction_id'], self.user_id, "TRX",
                                            "USDD_TRC20", deposit['value'])
                deposits_sum += float(deposit['value']) / pow(10, deposit['token_info']['decimals'])
        return deposits_sum

    async def get_trx_balance(self, deposits) -> float:
        url = f'https://apilist.tronscanapi.com/api/new/transfer?sort=-timestamp&count=true&limit=1000&start=0&address={self.trx_address}'
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if deposit.network == "TRX" and deposit.token_name is None]
        deposit_sum = 0.0
        for deposit in data['data']:
            if deposit['confirmed'] and deposit['transactionHash'] not in deposits and deposit[
                'transferToAddress'] == self.trx_address:
                await DepositService.create(deposit['transactionHash'], self.user_id, "TRX", None, deposit['amount'])
                deposit_sum += deposit['amount'] / pow(10, deposit['tokenInfo']['tokenDecimal'])
        return deposit_sum

    async def get_usdt_erc20_balance(self, deposits) -> float:
        url = f'https://api.ethplorer.io/getAddressHistory/{self.eth_address}?type=transfer&token=0xdAC17F958D2ee523a2206206994597C13D831ec7&apiKey={config.ETHPLORER_API_KEY}&limit=1000'
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if
                    deposit.network == "ETH" and deposit.token_name == "USDT_ERC20"]
        deposits_sum = 0.0
        for deposit in data['operations']:
            if deposit['transactionHash'] not in deposits and deposit['to'] == self.eth_address:
                await DepositService.create(deposit['transactionHash'], self.user_id, "ETH", "USDT_ERC20",
                                            deposit['value'])
                deposits_sum += float(deposit['value']) / pow(10, 6)
        return deposits_sum

    async def get_usdc_erc20_balance(self, deposits):
        url = f'https://api.ethplorer.io/getAddressHistory/{self.eth_address}?type=transfer&token=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48&apiKey={config.ETHPLORER_API_KEY}&limit=1000'
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if
                    deposit.network == "ETH" and deposit.token_name == "USDC_ERC20"]
        deposits_sum = 0.0
        for deposit in data['operations']:
            if deposit['transactionHash'] not in deposits and deposit['to'] == self.eth_address:
                await DepositService.create(deposit['transactionHash'], self.user_id, "ETH", "USDC_ERC20",
                                            deposit['value'])
                deposits_sum += float(deposit['value']) / pow(10, 6)
        return deposits_sum

    async def get_eth_balance(self, deposits):
        # TODO (fetch eth deposits)
        url = f'https://api.ethplorer.io/getAddressTransactions/{self.eth_address}?limit=1000&showZeroValues=false&apiKey={config.ETHPLORER_API_KEY}'
        data = await self.fetch_api_request(url)
        deposits = [deposit.tx_id for deposit in deposits if
                    deposit.network == "ETH" and deposit.token_name is None]
        deposits_sum = 0.0
        for deposit in data:
            if deposit['hash'] not in deposits and deposit['success'] is True and deposit['to'] == self.eth_address:
                await DepositService.create(deposit['hash'], self.user_id, "ETH", None,
                                            deposit['value'] * pow(10, 9))
                deposits_sum += deposit['value']
        return deposits_sum

    async def get_top_ups(self):
        user_deposits = await DepositService.get_by_user_id(self.user_id)
        balances = {"btc__deposit": await self.get_btc_balance(user_deposits),
                    "ltc__deposit": await self.get_ltc_balance(user_deposits),
                    "usdt_trc20_deposit": await self.get_usdt_trc20_balance(user_deposits),
                    "usdd_trc20_deposit": await self.get_usdd_trc20_balance(user_deposits),
                    "usdt_erc20_deposit": await self.get_usdt_erc20_balance(user_deposits),
                    "usdc_erc20_deposit": await self.get_usdc_erc20_balance(user_deposits)}
        return balances
    @staticmethod
    async def get_crypto_prices() -> dict[str, float]:
        # TODO("NEED API FOR USDD-TRC-20")
        usd_crypto_prices = {}
        urls = {
            "btc": 'https://api.kraken.com/0/public/Ticker?pair=BTCUSDT',
            "usdt": 'https://api.kraken.com/0/public/Ticker?pair=USDTUSD',
            "usdc": "https://api.kraken.com/0/public/Ticker?pair=USDCUSD",
            "ltc": 'https://api.kraken.com/0/public/Ticker?pair=LTCUSD',
            "eth": 'https://api.kraken.com/0/public/Ticker?pair=ETHUSD',
            "trx": "https://api.kraken.com/0/public/Ticker?pair=TRXUSD"
        }
        responses = (grequests.get(url) for url in urls.values())
        datas = grequests.map(responses)
        for symbol, data in zip(urls.keys(), datas):
            data = data.json()
            price = float(next(iter(data['result'].values()))['l'][1])
            usd_crypto_prices[symbol] = price
        usd_crypto_prices["usdd"] = 1.0  # 1USDD=1USD
        return usd_crypto_prices
