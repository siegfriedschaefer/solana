
from solana.rpc.api import Client
from solders.pubkey import Pubkey 
from solana.rpc.commitment import Commitment


import asyncio
import logging
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    print("You pressed Ctrl+C! Exiting...")
    sys.exit(0)


class SolanaTokenMonitor:

    def __init__(self, rpc_url: str, wallet_address: str):
        self.client = Client(rpc_url)
        self.wallet = Pubkey.from_string(wallet_address)  # Changed to Pubkey

        self.last_signature = None
        self.known_tokens = set()

    async def monitor_transactions(self):
        """Monitor wallet for new token transactions"""

        logger.info(f"Started monitoring wallet: {self.wallet}")

        while True:
            try:
                # Get recent transactions
                response = self.client.get_signatures_for_address(
                    self.wallet,
                    limit=10,
                    commitment="confirmed"
                )

                print(f"transactions: {response}")


                if not response.value:
                    logger.info(f"get_signatures_for_address returned no transactions")
                    await asyncio.sleep(10)
                    continue




                await asyncio.sleep(20)  # Poll every second

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(1)


    def start(self):
        """Start the monitor"""
        asyncio.run(self.monitor_transactions())



wallet_adresses = [
    '8JhckE5RX7pZno85WzGAPVdLfQ7po4MHmenwXzSockhx',
    '5GVJZ4Rn2zsfbGqw8ghMuYnvkPweW3d87mCEe18Hjuet',
    '7MzHTaQTArbEaj7KFyFVdqaQUwYqyJXuLub4bBrmKk7k',
]

def main():

    signal.signal(signal.SIGINT, signal_handler)

    # Your RPC endpoint (use your preferred node)
    RPC_URL = "https://api.mainnet-beta.solana.com"
        
    # Create and start monitor
    monitor = SolanaTokenMonitor(RPC_URL, wallet_adresses[0])
    monitor.start()

if __name__ == "__main__":
    main()

