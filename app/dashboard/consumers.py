import paramiko
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

class TerminalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(
            hostname="127.0.0.1",
            username="kristina",
            password="1425  ",
        )
        self.channel = self.ssh_client.invoke_shell()
        asyncio.create_task(self.receive_from_server())

    async def disconnect(self, close_code):
        self.channel.close()
        self.ssh_client.close()

    async def receive(self, text_data):
        self.channel.send(text_data)

    async def receive_from_server(self):
        while True:
            if self.channel.recv_ready():
                output = self.channel.recv(1024).decode("utf-8")
                await self.send(text_data=output)
            await asyncio.sleep(0.1)

