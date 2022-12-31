

import asyncio
import contextvars

import pytest


class TestContextVar:
    list_message: list[str] = []
    context_var_delay = contextvars.ContextVar("delay", default=1)
    const_text: str = "msg"

    async def coro_print(self):
        await asyncio.sleep(self.context_var_delay.get())
        self.list_message.append(f"{self.const_text}_{self.context_var_delay.get()}")

    @pytest.mark.asyncio
    async def test_context_var_basic(self):
        self.list_message.clear()
        self.list_message.append("start")
        list_task = [asyncio.create_task(self.coro_print(), name="first")]
        await asyncio.sleep(0)
        for i in range(2, 5):
            # Tasks support the contextvars module. When a Task is created it
            # copies the current context and later runs its coroutine in the
            # copied context.
            self.context_var_delay.set(i)
            task = asyncio.create_task(self.coro_print(),
                                       name=f"task delay {i}")
            list_task.append(task)
            await asyncio.sleep(0)
        done, pending = await asyncio.wait(list_task)
        self.list_message.append("stop")

        assert "start msg_1 msg_2 msg_3 msg_4 stop".split() == self.list_message
