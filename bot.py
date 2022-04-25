from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
import requests
import os
from dotenv import load_dotenv
from math import log10, floor

load_dotenv()

maiarDexGraphql = 'https://graph.maiar.exchange/graphql'

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_markdown_v2(fr'Hi {user.mention_markdown_v2()}\!')


def prices(update: Update, context: CallbackContext) -> None:
    pairs = getPairs()

    msg = "*Maiar Exchange Prices:*\n\n"

    for pair in pairs:
        msg += priceString(pair)
        if pair != pairs[-1]:
            msg += "\n  ───────\n"

    update.message.reply_markdown_v2(msg)


def price(update: Update, context: CallbackContext) -> None:
    #check if the user passed a token to search
    if len(context.args) == 0:
        update.message.reply_markdown_v2("You have to specify a token to get its price\.\nUsage example: /price MEX")
        return

    tokenToSearch = context.args[0]

    pairs = getPairs()
    pair = [pair for pair in pairs if tokenToSearch.upper()
            in pair["baseId"]]

    #check if the token has been found
    if len(pair) == 0:
        update.message.reply_markdown_v2("The token you specified has not been found\.\nPlease check the name and try again\.")
        return

    msg = "*Maiar Exchange Price:*\n\n" + priceString(pair[0])
    update.message.reply_markdown_v2(msg)


def pricediscovery(update: Update, context: CallbackContext) -> None:

    obj = {'query': 'query {\n\n  priceDiscoveryContracts {\n    launchedTokenAmount\n    launchedTokenPrice\n    launchedTokenPriceUSD\n    launchedTokenRedeemBalance\n    currentPhase {\n      name\n      penaltyPercent\n    }\n    launchedToken {\n      name\n      identifier\n    }\n  }\n}\n'}
    response = requests.post(maiarDexGraphql, data = obj).json()
    priceDiscoveryContract = response["data"]["priceDiscoveryContracts"][0]
    
    tokenPriceUsd = float(priceDiscoveryContract["launchedTokenPriceUSD"])
    tokenName = priceDiscoveryContract["launchedToken"]["name"]

    msg = f"*Current {tokenName} Discovered Price:*\n\n💰 `${str(round(tokenPriceUsd, 4))}` 💰"
    update.message.reply_markdown_v2(msg)


def priceString(pair):
    tokenName = pair["baseSymbol"]
    tokenPrice = pair["basePrice"]

    msg = f"*{tokenName}\:* 💰 `$"

    if tokenPrice < 1:
        msg += roundSmallNumber(tokenPrice)
    else:
        msg += str(round(tokenPrice, 2))

    msg += "`"
    return msg


def getPairs():
    pairs = requests.get('https://api.elrond.com/mex-pairs').json()
    return list(filter(isActivePair, pairs))  # filter non-active pairs


def isActivePair(pair):
    return pair["totalValue"] != 0


def roundSmallNumber(num):
    return str('%f' % float('%.4g' % num))


def main():
    updater = Updater(token=os.getenv('TELEGRAM_TOKEN'), use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("price", price))
    dispatcher.add_handler(CommandHandler("prices", prices))
    dispatcher.add_handler(CommandHandler("pricediscovery", pricediscovery))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
