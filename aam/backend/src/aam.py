
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

    async def get_token_info(self, mint_address: str) -> dict:
        """Get token metadata"""
        try:
            print("mint_address:")
            print(mint_address)

            response = self.client.get_account_info(mint_address)

            print("Tokensymbol:")
            print(response)

            # You might want to query token metadata programs for more info
            return {
                "mint": mint_address,
                "symbol": mint_address[:6]  # Simplified - you'd want to get actual token symbols
            }
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return {"mint": mint_address, "symbol": "UNKNOWN"}


    def parse_token_transfer(self, tx_data: dict) -> list:
        """Parse transaction for token transfers"""
        transfers = []
        
        try:

            meta = tx_data.transaction.meta
            if not meta:
                return transfers

            if meta.err == None:

                # print("pre_token_balances:")
                # print(meta.pre_token_balances)
                # print("post_token_balances:")
                # print(meta.post_token_balances)

                pre_tokens = {
                    acc.account_index: acc.ui_token_amount.ui_amount
                    for acc in meta.pre_token_balances
                }
   
                post_tokens = {
                    acc.account_index: acc.ui_token_amount.ui_amount
                    for acc in meta.post_token_balances
                }

                # Check account ownership and token program interactions
                for idx, acc in enumerate(tx_data.transaction.transaction.message.account_keys):

                    # todo if acc == str(self.wallet):
                    # this is just for testing
                    if acc != str(self.wallet):
                        pre_amount = pre_tokens.get(idx, 0)
                        post_amount = post_tokens.get(idx, 0)
                        
                        if pre_amount != post_amount:
                            mint = meta.pre_token_balances[0].mint if meta.pre_token_balances else None
                            if mint:
                                transfers.append({
                                    'mint': mint,
                                    'type': 'BUY' if post_amount > pre_amount else 'SELL',
                                    'amount': abs(post_amount - pre_amount),
                                    'timestamp': tx_data.block_time
                                })

        except Exception as e:
            logger.error(f"Error parsing transfer: {str(e)}")
            
        return transfers

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

                if not response.value:
                    logger.info(f"get_signatures_for_address returned no transactions")
                    await asyncio.sleep(10)
                    continue

                # Process new transactions
                for sig_info in reversed(response.value):
                    if self.last_signature == sig_info.signature:
                        break

                    # Get transaction details
                    tx = self.client.get_transaction(
                        sig_info.signature,
                        commitment="confirmed",
                        max_supported_transaction_version=0
                    )

                    if tx.value:
                        transfers = self.parse_token_transfer(tx.value)

                        for transfer in transfers:
                            # Get token info
                            token_info = await self.get_token_info(transfer['mint'])

                            print(token_info)

                    logger.info(f"transfers: {transfers}")

                    await asyncio.sleep(10)  # Poll every 10 seconds, not to fast for solana mainnet quotas

                await asyncio.sleep(20)  # Poll every second, not to fast for solana mainnet quotas

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

