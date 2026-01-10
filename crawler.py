import asyncio
import threading
import logging
from telethon import TelegramClient
from telethon.network.connection import ConnectionTcpAbridged
from config import Config

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)
logging.getLogger('telethon').setLevel(logging.DEBUG)

class TeleCrawler:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.client = TelegramClient(
            'conduit_v2', 
            Config.TG_API_ID, 
            Config.TG_API_HASH,
            connection=ConnectionTcpAbridged,
            loop=self.loop
        )
        self.current_qr_url = None
        self._auth_event = threading.Event()
        
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        # Schedule connection but don't block the start of run_forever
        self.loop.create_task(self._start_client())
        self.loop.run_forever()

    async def _start_client(self):
        print("Crawler: Connecting to Telegram...")
        try:
            # Try connecting with a timeout
            await asyncio.wait_for(self.client.connect(), timeout=20.0)
            print("Crawler: Connected.")
        except Exception as e:
            print(f"Crawler Connection Error: {e}")

    def is_authorized(self):
        if not self.client.is_connected():
            return False
        # If we are in the middle of QR login, we are NOT authorized yet
        if self.current_qr_url:
            return False
            
        try:
            # Use a very short timeout to avoid blocking Flask
            future = asyncio.run_coroutine_threadsafe(self.client.is_user_authorized(), self.loop)
            return future.result(timeout=1)
        except Exception:
            return False

    async def _qr_login_gen(self):
        """Async generator for QR login."""
        try:
            if not self.client.is_connected():
                print("Crawler: Not connected, attempting reconnect...")
                await self.client.connect()
            
            print("Crawler: Generating QR Login...")
            qr_login = await self.client.qr_login()
            print("Crawler: QR URL received.")
            self.current_qr_url = qr_login.url
            # Wait for user to scan
            await qr_login.wait()
            print("Crawler: QR Scanned! Login complete.")
            self.current_qr_url = None # Login complete
        except Exception as e:
            print(f"QR Login Error: {e}")
            self.current_qr_url = None

    def start_qr_login(self):
        """Triggers the QR login flow in the background."""
        if not self.is_authorized() and not self.current_qr_url:
             asyncio.run_coroutine_threadsafe(self._qr_login_gen(), self.loop)

    def get_qr_url(self):
        return self.current_qr_url

    async def _disconnect(self):
        await self.client.log_out()

    def logout(self):
        future = asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)
        return future.result()

crawler = TeleCrawler()
