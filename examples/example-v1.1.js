// Example of calculating fees in Terra Classic, 
// accounting for Terra Classic burn tax

import fetch from "isomorphic-fetch";
import {
  Coins,
  Fee,
  LCDClient,
  MnemonicKey,
  MsgSend,
} from "@terra-money/terra.js";


// Retrieve current gas prices
const gasPrices = await fetch("https://fcd.terra.dev/v1/txs/gas_prices");
const gasPricesJson = await gasPrices.json();
const gasPricesCoins = new Coins(gasPricesJson);

// Retrieve the tax rate and tax cap
const taxRateRaw = await fetch("https://rebel1.grouptwo.org/terra/treasury/v1beta1/tax_rate");
const taxRate = await taxRateRaw.json();
const taxCapRaw = await fetch("https://rebel1.grouptwo.org/terra/treasury/v1beta1/tax_caps/uluna");
const taxCap = await taxCapRaw.json();

// Connect to the LCD endpoint
const lcd = new LCDClient({
    URL: "https://rebel1.grouptwo.org",
    chainID: "rebel-2",
    isClassic: true,
});

const mk = new MnemonicKey({
      mnemonic: "Insert the mnemonic key of your test wallet here",
});

// Create a wallet with the specified mnemonic
const wallet = lcd.wallet(mk);

// Obtain the signing wallet data
const walletInfo = await wallet.accountNumberAndSequence();
const signerData = [{ sequenceNumber: walletInfo.sequence }];

// Set the send tx amount to 10 luna (10000000 uluna)
const txAmount = 10000000;

// Compute the burn tax amount for this transaction and convert to Coins
const taxAmount = Math.min(Math.ceil(txAmount * parseFloat(taxRate.tax_rate)), parseInt(taxCap.tax_cap));
const taxAmountCoins = new Coins({ uluna : taxAmount });
console.log("Burn tax amount: ", taxAmountCoins);

// Populate the send message
const send = new MsgSend(
    wallet.key.accAddress,
    "terra1l75p2y5rha7ru7389yqu4cn4yremerd57c4694",
    { uluna: txAmount.toString() });

// Estimate the gas amount and fee (without burn tax) for the message
var txFee = await lcd.tx.estimateFee(
    signerData,
    { msgs: [send], 
      gasPrices: gasPricesCoins, 
      gasAdjustment: 3, 
      feeDenoms: ["uluna"]
    }
);
console.log("Gas and Fee estimate, pre-tax:");
console.log(txFee);
console.log(txFee.amount)

// Add the burn tax component to the estimated fee
txFee.amount = txFee.amount.add(taxAmountCoins);
console.log("Gas and Fee estimate, post tax:");
console.log(txFee);
console.log(txFee.amount);

const tx = await wallet.createAndSignTx({ msgs: [send], fee: txFee });
const result = await lcd.tx.broadcast(tx);
console.log(result);