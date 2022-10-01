# layer2-dev-guidelines

The key issue in terra.js resides in estimateFee(): <br>
https://github.com/terra-rebels/terra.js/blob/main/src/client/lcd/api/TxAPI.ts#L270

This function is invoked when the "auto" gas calculation option is chosen, as per the official terra.js documentation. This function does not calculate the additional fee component required for the burn tax.

The original method of computing tax was deprecated when the stability tax was removed, and was never reinstated for the burn tax:<br>
https://github.com/terra-rebels/terra.js/blob/main/src/client/lcd/api/TxAPI.ts#L349

estimateFee() invokes estimateGas() to simulate the gas for the transaction using the LCD simulate API:<br>
https://github.com/terra-rebels/terra.js/blob/main/src/client/lcd/api/TxAPI.ts#L319

The issue for most dApp developers is that these calculations are hidden from them by using the recommended "auto" gas calculation method.

Instead of using the "auto" method, it is now necessary for dApp developers to separate out the gas computation and tax computations by invoking estimateFee() or estimateGas() directly, and then adding the 1.2% burn tax component (based on the value of the transaction being performed) in order to arrive at the correct transaction fee.

This result can then be passed as the transaction fee parameter to the transaction:
```
import { Fee } from '@terra-money/terra.js';

const msgs = [ new MsgSend( ... ), new MsgSwap( ... ), ]; // messages
const fee = new Fee(estimatedGas, { uluna: txFee });

const tx = await wallet.createAndSignTx({ msgs, fee });
```
https://github.com/terra-rebels/terra.js/blob/main/src/client/lcd/api/TxAPI.ts

The general mechanism for the calculation of the total transaction fee to be specified with a transaction, when the burn tax is active, is as follows:

```
estimatedGas = simulatedGas * gasAdjustment

gasTotal = estimatedGas * gasPrice
```
You can simulate a transaction in order to estimate the required total gas for that transaction type as described in the following LCD endpoint API documentation:
<br>
https://lcd.terra.dev/swagger/#/Service/Simulate

The API endpoint for the above is:
<br>
https://lcd.terra.dev/cosmos/tx/v1beta1/simulate

This endpoint only accepts a HTTP POST request method.

Please note that there is a bug in the simulate API such that it incorrectly simulates an amount of gas that is too low for certain transactions after the introduction of the Terra Classic burn tax.

The recommended workaround is to increase the gas adjustment value (see SDK references above) to 3 (the gas adjustment is just a multiplier to the gas value returned by the LCD simulate API).

This means more gas than necessary will be consumed, but will ensure the tx will not fail due to lack of gas.

The current gasPrices for different Terra denominations can be obtained from the following API endpoint:<br> 
https://fcd.terra.dev/v1/txs/gas_prices

The burn tax must also be accounted for as follows:
```
taxTotal= min((txAmount * taxRate), taxCap)
```
The current taxRate can be obtained from: <br>
https://lcd.terra.dev/terra/treasury/v1beta1/tax_rate

The current taxCap for uluna can be obtained from the following API:<br>
https://lcd.terra.dev/terra/treasury/v1beta1/tax_caps/uluna

Finally, the tx fee can be calculated as:
```
txFee = gasTotal + taxTotal
```
It is important to ensure consistency of denom units in uluna (micro luna) when calculating gasTotal, taxTotal, and txFee. 