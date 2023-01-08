

import aiohttp
import pytest
import yarl
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from yarl import URL


class TestHowToTestAIOHTTP:
    # https://docs.aiohttp.org/en/stable/testing.html#aiohttp-testing-writing-testable-services

    @pytest.mark.asyncio
    async def test_test_server_basic(self, aiohttp_client, loop):
        async def hello(request):
            return web.Response(text='Hello, world')

        app = web.Application()
        app.router.add_get('/', hello)
        client = await aiohttp_client(app)
        resp = await client.get('/')
        assert resp.status == 200
        text = await resp.text()
        assert 'Hello, world' in text

    @pytest.mark.asyncio
    async def test_aiohttp_server(self, aiohttp_server):
        # TestServer runs aiohttp.web.Application based server,
        # RawTestServer starts aiohttp.web.Server low level server.
        app = web.Application()
        # fill route table

        server = await aiohttp_server(app)
        assert server.started

    @pytest.mark.asyncio
    async def test_aiohttp_raw_server(
        self, aiohttp_raw_server,
        aiohttp_client
            ):
        # TestServer runs aiohttp.web.Application based server,
        # RawTestServer starts aiohttp.web.Server low level server.
        async def handler(request):
            return web.Response(text="OK")

        raw_server = await aiohttp_raw_server(handler)
        client = await aiohttp_client(raw_server)
        resp = await client.get('/')
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_unused_port(self, aiohttp_client, aiohttp_unused_port):
        port = aiohttp_unused_port()
        app = web.Application()
        # fill route table

        client = await aiohttp_client(app, server_kwargs={'port': port})
        assert isinstance(client, aiohttp.test_utils.TestClient)

    @pytest.mark.asyncio
    async def test_fake_request(self, aiohttp_client, aiohttp_unused_port):
        # We don’t recommend to apply make_mocked_request() everywhere
        # for testing web-handler’s business object – please use
        # test client and real networking via ‘localhost’
        # as shown in examples before.
        def handler(request):
            assert request.headers.get('token') == 'x'
            return web.Response(body=b'data')

        req = make_mocked_request('GET', '/', headers={'token': 'x'})
        resp = handler(req)
        assert resp.body == b'data'


class TestBasic:

    @pytest.mark.asyncio
    async def test_route_add(self, aiohttp_client):
        async def hello(request):
            return web.Response(text="Hello, world")

        app = web.Application()
        app.add_routes([web.get('/', hello)])
        client = await aiohttp_client(app)

        resp = await client.get('/')
        assert resp.status == 200
        assert await resp.text() == "Hello, world"

    @pytest.mark.asyncio
    async def test_route_decorator(self, aiohttp_client):
        routes = web.RouteTableDef()

        @routes.get('/decor')
        async def handler_decor(request):
            return web.Response(text="decorator route")

        app = web.Application()
        app.add_routes(routes)
        client = await aiohttp_client(app)

        resp = await client.get("/decor")
        assert resp.status == 200
        assert await resp.text() == "decorator route"

    @pytest.mark.asyncio
    async def test_route_wildcard(self, aiohttp_client):
        async def hello(request):
            return web.Response(text="success")

        app = web.Application()
        app.add_routes([web.route("*", '/path', hello)])
        client = await aiohttp_client(app)

        resp = await client.get('/path')
        assert resp.status == 200
        assert await resp.text() == "success"

        resp = await client.post('/path')
        assert resp.status == 200
        assert await resp.text() == "success"

    @pytest.mark.asyncio
    async def test_variable_name_simple(self, aiohttp_client):
        routes = web.RouteTableDef()

        @routes.get('/{name}')
        async def variable_handler(request):
            return web.Response(
                text="Hello, {}".format(request.match_info['name']))

        app = web.Application()
        app.add_routes(routes)
        client = await aiohttp_client(app)

        resp = await client.get("/test_name")
        assert resp.status == 200
        assert await resp.text() == "Hello, test_name"

    @pytest.mark.asyncio
    async def test_variable_name_wich_reg(self, aiohttp_client):
        # By default, each part matches the regular expression [^{}/]+.
        # You can also specify a custom regex in the form {identifier:regex}:
        routes = web.RouteTableDef()

        @routes.get(r'/{name:\d+}')
        async def variable_handler(request):
            return web.Response(
                text="Hello, {}".format(request.match_info['name']))

        app = web.Application()
        app.add_routes(routes)
        client = await aiohttp_client(app)

        resp = await client.get("/test_name")
        assert resp.status == 404

        resp = await client.get("/1234567890")
        assert resp.status == 200
        assert await resp.text() == "Hello, 1234567890"

    @pytest.mark.asyncio
    async def test_reverse_url(self, aiohttp_client):
        routes = web.RouteTableDef()

        @routes.get('/root', name="root_name")
        async def variable_handler(request):
            return web.Response(
                text="Test")

        @routes.get(r'/{user}/info', name='user-info')
        async def handler_wich_variable(request):
            return web.Response(
                text="Hello, {}".format(request.match_info['name']))

        app = web.Application()
        app.add_routes(routes)

        url = app.router['root_name'].url_for().\
            with_query({"a": "b", "c": "d"})
        assert isinstance(url, yarl.URL)
        assert url == URL('/root?a=b&c=d')

        url = app.router['user-info'].url_for(user='john_doe')
        assert url == URL("/john_doe/info")
        url_with_qs = url.with_query("a=b")
        assert url_with_qs == URL('/john_doe/info?a=b')
