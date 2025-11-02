import asyncio
import discord
import random
import signal
import sys

# Load tokens and messages
try:
    with open('tokens.txt', 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
    with open('spam_messages.txt', 'r') as f:
        spam_msgs = [line.strip() for line in f if line.strip()]
except FileNotFoundError as e:
    print(f"File missing: {e}")
    sys.exit(1)

# Global state
running = False
channel_id = None
clients = []

def signal_handler():
    print("\nShutting down...")
    for client in clients:
        client.loop.call_soon_threadsafe(client.loop.stop)
    sys.exit(0)

signal.signal(signal.SIGINT, lambda s, f: signal_handler())

class SelfBot(discord.Client):
    def __init__(self, token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = token
        self.spam_task = None
        self.name_task = None

    async def on_connect(self):
        print(f'{self.user} connected.')

    async def on_ready(self):
        print(f'{self.user} ready to spam.')
        clients.append(self)
        await self.start_spamming()

    async def start_spamming(self):
        self.spam_task = asyncio.create_task(self.spam_loop())
        self.name_task = asyncio.create_task(self.name_change_loop())

    async def spam_loop(self):
        if not channel_id or not running:
            return
        channel = self.get_channel(int(channel_id))
        if not channel:
            return
        while running:
            msg = random.choice(spam_msgs)
            try:
                await channel.send(msg)
            except:
                pass
            await asyncio.sleep(random.uniform(0.5, 1.0))

    async def name_change_loop(self):
        if not channel_id or not running:
            return
        channel = self.get_channel(int(channel_id))
        if not isinstance(channel, discord.GroupChannel):
            return
        while running:
            new_name = random.choice(spam_msgs)[:32]
            try:
                await channel.edit(name=new_name)
            except:
                pass
            await asyncio.sleep(3)

    async def stop(self):
        if self.spam_task:
            self.spam_task.cancel()
        if self.name_task:
            self.name_task.cancel()
        await self.close()

async def start_spam():
    global running
    if running:
        print("Already running.")
        return
    running = True
    print(f"UNSTOPPABLE ON → Channel ID: {channel_id}")

    
    intents = discord.Intents.none()
    intents.guilds = True
    intents.messages = True
    # DO NOT touch message_content – selfbots doesnt have it

    for token in tokens:
        try:
            client = SelfBot(token, intents=intents)
            asyncio.create_task(client.start(token, bot=False))
        except Exception as e:
            print(f"Failed to start token: {e}")

async def stop_spam():
    global running
    running = False
    print("Stopping all clients...")
    for client in clients[:]:
        try:
            await client.stop()
        except:
            pass
    clients.clear()

async def console_listener():
    global channel_id
    while True:
        try:
            cmd = await asyncio.to_thread(input)
            cmd = cmd.strip()

            if cmd.startswith('.unstoppable '):
                channel_id = cmd.split(' ', 1)[1]
                await start_spam()

            elif cmd == '.unstoppableend':
                await stop_spam()

            else:
                print("Use: .unstoppable <channel_id> | .unstoppableend")

        except EOFError:
            break
        except Exception as e:
            print(f"Console error: {e}")

async def main():
    if not tokens:
        print("No tokens in tokens.txt")
        return
    if not spam_msgs:
        print("No messages in spam_messages.txt")
        return

    print(f"Loaded {len(tokens)} tokens | {len(spam_msgs)} messages")
    print("Type .unstoppable <channel_id> to start")

    await console_listener()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        signal_handler()