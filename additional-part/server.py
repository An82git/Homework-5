import asyncio
import logging
import websockets
import names
import aiofile
from aiopath import AsyncPath
import datetime
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from exchange import create_session, CURRENCY_LIST


logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]
    
    async def create_data_file(self, data_name:str) -> AsyncPath:
        data_dir = AsyncPath("storage/")
        data_file = AsyncPath(f"storage/{data_name}")
        
        if not await data_dir.exists():
            await data_dir.mkdir()
        
        if not await data_file.exists():
            await data_file.touch()

        return data_file
    
    async def log_command(self, 
                          command:str, 
                          user_name:str, 
                          function = None, 
                          arg:list = [], 
                          data_file:str = "",
                          error = None):
        
        code = await function(*arg) if function else None

        time = datetime.datetime.now()
               
        log_text = f"{time}: [user: {user_name}; command: {command}; code: {code if not error else False}; error: {error}]\n"

        data = await self.create_data_file(data_file)

        async with aiofile.async_open(data, "a") as file:
            await file.write(log_text)

    
    async def exchange_command(self, num:int = 1) -> bool:
        await self.send_to_clients("{:-^20}".format("loading"))
        data = await create_session(num, CURRENCY_LIST)
        await self.send_to_clients(f"Currency exchange rate")

        for el in data:
            for date, value in el.items():
                await self.send_to_clients("{:-^20}".format(date))
                await self.send_to_clients("{:^6}|{:^6}|{:^6}".format("Curr","Sale","Buy"))
                for key, value in value.items():
                    await self.send_to_clients("{:^6}|{:^6}|{:^6}".format(key,value["sale"],value["purchase"]))
        return True
        

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            
            await self.send_to_clients(f"{ws.name}: {message}")

            if message[0] == "/":
                l = message.split(" ")

                if l[0] == "/exchange":
                    arg = l[1] if len(l) > 1 else "1"
                
                    if not arg.isdigit():
                        await self.send_to_clients(f"'{l[1]}' is not a number.")
                        
                        await self.log_command(
                            message,
                            ws.name,
                            data_file="data-log.txt",
                            error=f"'{l[1]}' is not a number.")

                    else:
                        await self.log_command(
                            message,              
                            ws.name, 
                            function=self.exchange_command, 
                            arg=[int(arg)], 
                            data_file="data-log.txt"
                            )


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 5000):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
