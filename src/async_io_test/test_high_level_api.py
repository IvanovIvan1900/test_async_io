import asyncio
from datetime import datetime, time
from time import sleep

import pytest

# https://docs-python.ru/standart-library/modul-asyncio-python/vkljuchenie-rezhima-otladki-asyncio/
DEBUG = True


class TestRun:

    def test_run(self):
        async def test_func(list_message: list[str]):
            await asyncio.sleep(1)
            list_message.append("run")
        list_message = ["start"]
        asyncio.run(test_func(list_message), debug=DEBUG)
        list_message.append("stop")

        assert ["start", "run", "stop"] == list_message

    # only 3.11
    @pytest.mark.py311
    def test_runner(self):
        async def test_func(list_message: list[str], n: int):
            await asyncio.sleep(1)
            list_message.append(f"run {n}")
        list_message = ["start"]
        with asyncio.Runner(debug=DEBUG) as runner:
            runner.run(test_func(list_message, 1))
            runner.run(test_func(list_message, 2))
        list_message.append("stop")

        assert ["start", "run 1", "run 2", "stop"] == list_message


class TestCoroutineAndTasks:
    list_message: list[str] = []

    async def coro_hello(self, delay_sec: int, message: str,
                         ):
        await asyncio.sleep(delay_sec)
        self.list_message.append(message)

    async def coro_chancell(self, delay_sec: int):
        await asyncio.sleep(delay_sec)
        self.list_message.append("cancel")
        raise asyncio.CancelledError

    @pytest.mark.asyncio
    async def test_coroutines(self):
        # корутины выполняться последовательно
        self.list_message.clear()
        self.list_message.append("start")
        time_start = datetime.now()
        await self.coro_hello(1, "hello")
        await self.coro_hello(2, "world")
        time_stop = datetime.now()
        self.list_message.append("stop")
        assert int((time_stop-time_start).total_seconds()) == 3
        assert "start hello world stop".split() == self.list_message

    @pytest.mark.asyncio
    async def test_tasks(self):
        self.list_message.clear()
        self.list_message.append("start")
        task1 = asyncio.create_task(self.coro_hello(1, "hello"))
        task2 = asyncio.create_task(self.coro_hello(2, "world"))

        time_start = datetime.now()
        await task1
        await task2
        time_stop = datetime.now()
        self.list_message.append("stop")
        assert int((time_stop-time_start).total_seconds()) == 2
        assert "start hello world stop".split() == self.list_message

    @pytest.mark.asyncio
    async def test_gather_and_cancel_task(self):
        self.list_message.clear()
        self.list_message.append("start")
        res = await asyncio.gather(self.coro_hello(2, "hello"),
                                   self.coro_chancell(1),
                                   return_exceptions=True)
        self.list_message.append("stop")
        assert len(res) == 2
        assert res[0] is None
        assert type(res[1]) == asyncio.CancelledError
        assert "start cancel hello stop".split() == self.list_message

    @pytest.mark.asyncio
    async def test_gather_and_cancel_task_wichout_return_exception(self):
        self.list_message.clear()
        self.list_message.append("start")
        try:
            res = await asyncio.gather(self.coro_hello(2, "hello"),
                                       self.coro_chancell(1),
                                       return_exceptions=False)
        except asyncio.CancelledError:
            self.list_message.append("exception")
        self.list_message.append("stop")
        assert "start cancel exception stop".split() == self.list_message

    @pytest.mark.asyncio
    async def test_shield(self):
        # https://docs-python.ru/standart-library/modul-asyncio-python/funktsija-shield-modulja-asyncio/
        async def cancel_task(aw, list_message: list[str]):
            await asyncio.sleep(1)
            aw.cancel()
            list_message.append("cancel")

        self.list_message.clear()
        self.list_message.append("start")
        real_task = asyncio.create_task(self.coro_hello(2, "hello"))
        shield = asyncio.shield(real_task)
        asyncio.create_task(cancel_task(shield, self.list_message))
        await real_task
        self.list_message.append("stop")
        assert not real_task.cancelled()
        assert shield.cancelled()
        assert "start cancel hello stop".split() == self.list_message

    @pytest.mark.asyncio
    async def test_timeout_basic(self):
        self.list_message.clear()
        self.list_message.append("start")
        delay_int_or_float_sec = 2.5
        task = self.coro_hello(5, "hello")
        try:
            async with asyncio.timeout(delay_int_or_float_sec):
                await task
        except TimeoutError:
            self.list_message.append("timout")
        self.list_message.append("stop")
        assert "start timout stop".split() == self.list_message

    @pytest.mark.py311
    @pytest.mark.asyncio
    async def test_timeout_reshedule(self):
        self.list_message.clear()
        self.list_message.append("start")
        task = self.coro_hello(5, "hello")
        try:
            async with asyncio.timeout(None) as cm:
                new_deadline = asyncio.get_running_loop().time() + 10
                cm.reschedule(new_deadline)
                await task
        except TimeoutError:
            self.list_message.append("timout")
        self.list_message.append("stop")
        if not cm.expired():
            self.list_message.append("not_expired")
        assert "start hello stop not_expired".split() == self.list_message

    @pytest.mark.asyncio
    async def test_wait_for(self):
        self.list_message.clear()
        self.list_message.append("start")
        delay_int_or_float_sec = 2.5
        task = self.coro_hello(5, "hello")
        try:
            await asyncio.wait_for(task, delay_int_or_float_sec)
        except TimeoutError:
            self.list_message.append("timout")
        self.list_message.append("stop")
        assert "start timout stop".split() == self.list_message


class TestToTread:
    list_message: list[str] = []

    def func_blocking_io(self, delay: int, text_data: str):
        sleep(delay)
        self.list_message.append(text_data)

    async def coro_hello(self, delay_sec: int, message: str,
                         ):
        await asyncio.sleep(delay_sec)
        self.list_message.append(message)

    @pytest.mark.asyncio
    async def test_run_in_thread(self):
        self.list_message.clear()
        self.list_message.append("start")
        await asyncio.gather(
            asyncio.to_thread(self.func_blocking_io, delay=4,
                              text_data="block_io"),
            self.coro_hello(1, "hello")
            )
        self.list_message.append("stop")
        assert "start hello block_io stop".split() == self.list_message


class TestTask:
    