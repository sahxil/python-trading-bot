# main.py
import config
from bot import BasicBot

def main():
    """Main function to run the bot."""
    print("Bot starting...")
    bot = BasicBot(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
        base_url=config.BASE_URL
    )

    account_info = bot.get_account_info()

    if account_info:
        print("Successfully connected to Binance.")
        # We can print specific details later, e.g., balances
        print("Account balances:")
        for asset in account_info.get('assets', []):
            if float(asset['walletBalance']) > 0:
                print(f"  {asset['asset']}: {asset['walletBalance']}")
    else:
        print("Failed to connect to Binance. Please check your API keys and network connection.")

if __name__ == "__main__":
    main()