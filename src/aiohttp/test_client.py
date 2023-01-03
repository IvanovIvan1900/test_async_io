
import aiofiles
import aiohttp
import orjson
import pytest
import ujson


class TestRequest:

    @pytest.mark.asyncio
    async def test_request_basic(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('http://httpbin.org/get') as resp:
                assert resp.status == 200
                # print(resp.status)
                # print(await resp.text())

    @pytest.mark.asyncio
    async def test_many_request_one_site(self):
        async with aiohttp.ClientSession('http://httpbin.org') as session:
            async with session.get('/get') as resp:
                assert resp.status == 200
            async with session.post('/post', data=b'data') as resp:
                assert resp.status == 200
            async with session.put('/put', data=b'data') as resp:
                assert resp.status == 200

    @pytest.mark.asyncio
    async def test_request_wich_param(self):
        async with aiohttp.ClientSession() as session:
            params = {'key1': 'value1', 'key2': 'value2'}
            async with session.get('http://httpbin.org/get',
                                   params=params) as resp:
                expect = 'http://httpbin.org/get?key1=value1&key2=value2'
                assert str(resp.url) == expect

    @pytest.mark.asyncio
    async def test_request_wich_two_value_one_key(self):
        async with aiohttp.ClientSession() as session:
            params = [('key', 'value1'), ('key', 'value2')]
            async with session.get('http://httpbin.org/get',
                                   params=params) as r:
                expect = 'http://httpbin.org/get?key=value1&key=value2'
                assert str(r.url) == expect

    @pytest.mark.asyncio
    async def test_request_json(self):
        # если не указать json_serialize - будет использован
        # стандартный json модуль
        async with aiohttp.ClientSession(
            "http://httpbin.org",
            json_serialize=ujson.dumps
        ) as session:
            resp = await session.get("/get", json={'test': 'object'})
            assert resp.status == 200
            resp_json = await resp.json()
            assert isinstance(resp_json, dict)

    @pytest.mark.asyncio
    async def test_request_file(self, tmp_path_factory):
        temp_file = tmp_path_factory.mktemp("aiohttp") / "test_data.txt"
        with open(temp_file, mode='w') as f:
            f.write("Test str 1")
            f.write("test str 2")

        url = 'http://httpbin.org/post'
        files = {'file': open(temp_file, 'rb')}

        async with aiohttp.ClientSession() as session:
            resp = await session.post(url, data=files)
            assert resp.status == 200

    @pytest.mark.asyncio
    async def test_request_streaming_upload(self, tmp_path_factory):
        # aiohttp supports multiple types of streaming uploads,
        # which allows you to send large files without
        # reading them into memory.
        temp_file = tmp_path_factory.mktemp("aiohttp") / "huge_files.txt"
        with open(temp_file, mode='w') as f:
            f.write("Test str 1")
            f.write("test str 2")

        async def file_sender(file_name=None):
            async with aiofiles.open(file_name, 'rb') as f:
                chunk = await f.read(64*1024)
                while chunk:
                    yield chunk
                    chunk = await f.read(64*1024)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://httpbin.org/post',
                data=file_sender(file_name=temp_file)
            ) as resp:
                assert resp.status == 200

    @pytest.mark.asyncio
    async def test_request_timeouts(self):
        timeout = aiohttp.ClientTimeout(
            total=5*60, connect=None,
            sock_connect=None, sock_read=None
            )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('http://httpbin.org/get') as resp:
                assert resp.status == 200


class TestResponse:

    @pytest.mark.asyncio
    async def test_response_text(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.github.com/events') as resp:
                assert resp.status == 200
                resp_text = await resp.text()
                assert isinstance(resp_text, str)
                # or define encoding
                await resp.text(encoding='utf-8')

    @pytest.mark.asyncio
    async def test_response_binary(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.github.com/events') as resp:
                assert resp.status == 200
                resp_bytes = await resp.read()
                assert isinstance(resp_bytes, bytes)

    @pytest.mark.asyncio
    async def test_response_json(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.github.com/events') as resp:
                resp_json = await resp.json()
                assert isinstance(resp_json, list)

    @pytest.mark.asyncio
    async def test_response_chunk(self, tmp_path_factory):
        temp_file = tmp_path_factory.mktemp("aiohttp") / "resp_chunk.txt"
        chunk_size = 10
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.github.com/events') as resp:
                with open(temp_file, 'wb') as fd:
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        fd.write(chunk)
