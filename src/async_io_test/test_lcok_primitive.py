import asyncio
import datetime

import pytest


class TestLock:

    @pytest.mark.asyncio
    async def test_lock_basic(self):
        lock = asyncio.Lock()
        assert not lock.locked()
        # ... later
        async with lock:
            # exclusive acces
            assert lock.locked()

        assert not lock.locked()


class TestEvent:
    list_message: list[str] = []

    async def coro_wait(self, delay: int, msg: str, event: asyncio.Event):
        await event.wait()
        await asyncio.sleep(delay)
        self.list_message.append(msg)

    @pytest.mark.asyncio
    async def test_event_basic(self):
        self.list_message.clear()
        event = asyncio.Event()
        task1 = asyncio.create_task(self.coro_wait(1, "first", event))
        task2 = asyncio.create_task(self.coro_wait(2, "two", event))
        event.set()
        self.list_message.append("start")
        res = await asyncio.gather(task1, task2)
        self.list_message.append("stop")
        assert len(res) == 2
        assert "start first two stop".split() == self.list_message


class TestSemaphore:
    list_message: list[str] = []
    sem: asyncio.Semaphore = None
    date_time_start: datetime.datetime = None

    async def coro_acq_sem(self):
        async with self.sem:
            await asyncio.sleep(1)
            sec_from_start = int((datetime.datetime.now() - self.date_time_start).total_seconds())
            self.list_message.append(f"sec_from_start_{sec_from_start}")

    @pytest.mark.asyncio
    async def test_semaphore_basic(self):
        self.list_message.clear()
        task_1 = asyncio.create_task(self.coro_acq_sem())
        task_2 = asyncio.create_task(self.coro_acq_sem())
        task_3 = asyncio.create_task(self.coro_acq_sem())
        task_4 = asyncio.create_task(self.coro_acq_sem())
        task_5 = asyncio.create_task(self.coro_acq_sem())
        self.sem = asyncio.Semaphore(2)
        self.list_message.append("start")
        self.date_time_start = datetime.datetime.now()
        res = await asyncio.gather(task_1, task_2, task_3, task_4, task_5)
        self.list_message.append("stop")

        assert len(res) == 5
        assert "start sec_from_start_1 sec_from_start_1 sec_from_start_2 sec_from_start_2 sec_from_start_3 stop".split() == self.list_message


class TestBarrier:
    list_message: list[str] = []
    date_time_start: datetime.datetime = None
    barrier: asyncio.Barrier = None

    async def coro_wait(self):
        await self.barrier.wait()
        sec_from_start = int((datetime.datetime.now() - self.date_time_start).total_seconds())
        self.list_message.append(f"sec_from_start_{sec_from_start}")

    @pytest.mark.asyncio
    async def test_barrier_basic(self):
        """ тут сразу несколько моментов:
            1. Если мы создаем несколько Task, то при первом await они все запускаются на выполнение, без всякого gather
            2. После того как 3 такси встали у барьера - счетчик сбрасывается, поэтому четвертая задача так и не будет выполнена"""
        self.list_message.clear()
        self.barrier = asyncio.Barrier(3)
        self.list_message.append("start")
        self.date_time_start = datetime.datetime.now()
        n = 4
        list_task: list[asyncio.Task] = []
        while n > 0:
            list_task.append(asyncio.create_task(self.coro_wait()))
            await asyncio.sleep(1)
            n -= 1
        self.list_message.append("stop")

        assert "start sec_from_start_2 sec_from_start_2 sec_from_start_2 stop".split() == self.list_message
