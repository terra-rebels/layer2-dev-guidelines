from terra_sdk.client.lcd import LCDClient
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.core.bank import MsgSend
from terra_sdk.core.coins import Coins, Coin
from terra_sdk.client.lcd.api.tx import CreateTxOptions, SignerOptions

import requests
import math

# the python lib does not know about the classic and testnet yet, add following lines to lcdclient.py at line 43 to add them:
# if chain_id == "rebel-2":
#     return [Coins.from_str("0.15uluna"), Numeric.parse(1.75)]
# if chain_id == "columbus-5":
#     return [Coins.from_str("0.15uluna"), Numeric.parse(1.75)]

sourceMnemonicKey = MnemonicKey("Insert the mnemonic key of your test wallet here")
targetAddress = 'terra1euprf4y086nsghdshrp9nks6tjx0qnv9mpu47t'
chain_id = "rebel-2"
lcdURL = "https://rebel1.grouptwo.org/"
txAmount = 10000000


terra = LCDClient(
    chain_id=chain_id,
    url=lcdURL
)

# Retrieve current gas prices
gasPrices = requests.get("https://fcd.terra.dev/v1/txs/gas_prices")
gasPricesJson = gasPrices.json()
gasPricesCoins = Coins(gasPricesJson)

# Retrieve the tax rate and tax cap
taxRateRaw = requests.get(lcdURL+"/terra/treasury/v1beta1/tax_rate")
taxRate = taxRateRaw.json()
taxCapRaw = requests.get(lcdURL+"/terra/treasury/v1beta1/tax_caps/uluna")
taxCap = taxCapRaw.json()

# Compute the burn tax amount for this transaction and convert to Coins
taxAmount = min(math.ceil(int(txAmount) * float(taxRate["tax_rate"])), int(taxCap["tax_cap"]))

taxAmountCoins = Coins(str(taxAmount)+"uluna")
print("Burn tax amount: ", taxAmountCoins)

# create the send message
send = MsgSend(
    sourceMnemonicKey.acc_address,
    targetAddress,
    amount=Coins([Coin("uluna", txAmount)])
)

wallet = terra.wallet(sourceMnemonicKey)
walletInfo = wallet.account_number_and_sequence()

signer_opt = SignerOptions(
    address=MnemonicKey.acc_address,
    sequence=walletInfo["sequence"]
)

# Estimate the gas amount and fee (without burn tax) for the message
txFee = terra.tx.estimate_fee(
    [signer_opt],
    CreateTxOptions(
        msgs=[send],
        gas_prices = gasPricesCoins,
        gas_adjustment = "3",
        fee_denoms = ["uluna"]
    )
)

# Add the burn tax component to the estimated fee
txFee.amount = txFee.amount.add(taxAmountCoins)

# create and sign the actual transaction with calculated gas prices including tax
tx = wallet.create_and_sign_tx(
    CreateTxOptions(
        msgs=[send],
        memo = "thisIsATest", # Optional,
        fee = txFee
    )
)

# broadcast the transaction
result = terra.tx.broadcast(tx)
print(result)