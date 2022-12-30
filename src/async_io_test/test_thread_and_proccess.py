import asyncio
import concurrent.futures


class TestRunInThreadAndPorcces:
    # https://docs.python.org/3/library/asyncio-eventloop.html
    list_message: list[str] = []

    def blocking_io(self):
        # File operations (such as logging) can block the
        # event loop: run them in a thread pool.
        with open('/dev/urandom', 'rb') as f:
            return f.read(100)

    def cpu_bound(self):
        # CPU-bound operations will block the event loop:
        # in general it is preferable to run them in a
        # process pool.
        return sum(i * i for i in range(10 ** 7))

    async def main(self):
        self.list_message.clear()
        loop = asyncio.get_running_loop()
        # Options:
        # 1. Run in the default loop's executor:
        result = await loop.run_in_executor(
            None, self.blocking_io)
        # print('default thread pool', result)
        self.list_message.append(f"result in loop {result}")
        # 2. Run in a custom thread pool:
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool, self.blocking_io)
            # print('custom thread pool', result)
            self.list_message.append(f"result in thread {result}")

        # 3. Run in a custom process pool:
        with concurrent.futures.ProcessPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool, self.cpu_bound)
            # print('custom process pool', result)
            self.list_message.append(f"result in procces {result}")

    # @pytest.mark.asyncio
    def test_run(self):
        asyncio.run(self.main())
