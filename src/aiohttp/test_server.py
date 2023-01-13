

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
    async def test_json_response(self, aiohttp_client):
        async def hello(request):
            data = {"key": "value"}
            return web.json_response(data)

        app = web.Application()
        app.add_routes([web.route("*", '/test_json', hello)])
        client = await aiohttp_client(app)

        resp = await client.get('/test_json')
        assert resp.status == 200
        assert resp.content_type == "application/json"
        assert await resp.json() == {"key": "value"}


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

    @pytest.mark.asyncio
    async def test_class_based_view(self, aiohttp_client):
        routes = web.RouteTableDef()

        @routes.get('/root', name="root_name")
        class MyView(web.View):

            async def get(self):
                request = self.request
                return web.Response(text="CBW get")

            async def post(self):
                return web.Response(text="CBW post")

        app = web.Application()
        app.add_routes(routes)
        client = await aiohttp_client(app)

        resp = await client.get("/root")
        assert resp.status == 200
        assert await resp.text() == "CBW get"

        resp = await client.put("/root")
        assert resp.status == 405

    @pytest.mark.asyncio
    async def test_view_route_resource(self, aiohttp_client):
        routes = web.RouteTableDef()

        @routes.get('/root')
        async def variable_handler(request):
            return web.Response(
                text="Test")

        @routes.get(r'/{user}/info', name='user-info')
        async def handler_wich_variable(request):
            return web.Response(
                text="Hello, {}".format(request.match_info['name']))

        app = web.Application()
        app.add_routes(routes)

        # All registered resources in a router can be
        # viewed using the UrlDispatcher.resources() method:
        assert len(app.router.resources()) == 2
        for route in app.router.resources():
            assert isinstance(
                route,
                (
                    aiohttp.web_urldispatcher.PlainResource,
                    aiohttp.web_urldispatcher.DynamicResource,
                ),
            )

        # A subset of the resources that were registered
        # with a name can be viewed using the
        # UrlDispatcher.named_resources() method:
        assert len(app.router.named_resources().items()) == 1
        for name, resource in app.router.named_resources().items():
            assert isinstance(name, str)

    @pytest.mark.asyncio
    async def test_session(self, aiohttp_client):
        import base64

        from aiohttp import web
        from aiohttp_session import get_session, setup
        from aiohttp_session.cookie_storage import EncryptedCookieStorage
        from cryptography import fernet

        async def handler(request):
            session = await get_session(request)
            last_visit = session['count_visit']\
                if 'count_visit' in session else 1
            text = f'visit :{last_visit}'
            session['count_visit'] = last_visit + 1
            return web.Response(text=text)

        async def make_app():
            app = web.Application()
            # secret_key must be 32 url-safe base64-encoded bytes
            fernet_key = fernet.Fernet.generate_key()
            secret_key = base64.urlsafe_b64decode(fernet_key)
            setup(app, EncryptedCookieStorage(secret_key))
            app.add_routes([web.get('/', handler)])
            return app

        client = await aiohttp_client(await make_app())

        resp = await client.get("/")
        assert resp.status == 200
        assert await resp.text() == "visit :1"

        resp = await client.get("/")
        assert resp.status == 200
        assert await resp.text() == "visit :2"

    @pytest.mark.asyncio
    async def test_global_variable(self, aiohttp_client):
        async def hello(request):
            data = {"my_private_key": request.app["my_private_key"]}
            return web.json_response(data)

        app = web.Application()
        app['my_private_key'] = "my_data_value"
        app.add_routes([web.route("*", '/', hello)])
        client = await aiohttp_client(app)

        resp = await client.get('/')
        assert resp.status == 200
        resp_json = await resp.json()
        assert resp_json["my_private_key"] == app['my_private_key']

    @pytest.mark.asyncio
    async def test_test_context_var(self, aiohttp_client):
        # у корутин выполнящихся при запуске, остановке и очистки конктекста сервера
        #       - одно и то же пространство
        # а вот у каждого хандлера - свое,

        from contextvars import ContextVar

        from aiohttp import web

        VAR = ContextVar('VAR', default='default')
        list_message: list[str] = []

        async def coro():
            return VAR.get()

        async def handler(request):
            var = f"3. {VAR.get()}"
            VAR.set('handler')
            ret = await coro()
            return web.Response(text='->'.join([var,
                                                f"4. {ret}"]))

        async def on_startup(app):
            list_message.append(f'2. on_startup {VAR.get()}')
            VAR.set('on_startup')

        async def on_cleanup(app):
            list_message.append(f'5. on_cleanup {VAR.get()}')
            VAR.set('on_cleanup')

        async def init():
            list_message.append(f'1. init {VAR.get()}')
            VAR.set('init')
            app = web.Application()
            app.router.add_get('/', handler)

            app.on_startup.append(on_startup)
            app.on_cleanup.append(on_cleanup)
            return app

        client = await aiohttp_client(await init())
        resp = await client.get("/")
        list_message.append(await resp.text())
        await client.close()
        assert "1. init default=2. on_startup init=3. on_startup->4. handler=5. on_cleanup on_startup".split("=") == list_message

    @pytest.mark.asyncio
    async def test_middleware(self, aiohttp_client):
        from aiohttp import web
        list_message: list[str] = []

        async def test(request):
            list_message.append('Handler function called')
            return web.Response(text="Hello")

        @web.middleware
        async def middleware1(request, handler):
            list_message.append('Middleware 1 called')
            response = await handler(request)
            list_message.append('Middleware 1 finished')
            return response

        @web.middleware
        async def middleware2(request, handler):
            list_message.append('Middleware 2 called')
            response = await handler(request)
            list_message.append('Middleware 2 finished')
            return response

        app = web.Application(middlewares=[middleware1, middleware2])
        app.router.add_get('/', test)
        client = await aiohttp_client(app)
        resp = await client.get("/")
        assert resp.status == 200
        assert 'Middleware 1 called=Middleware 2 called=Handler function called=Middleware 2 finished=Middleware 1 finished'.split("=") == list_message

    @pytest.mark.asyncio
    async def test_middleware_factory(self, aiohttp_client):
        from aiohttp import web

        async def test(request):
            return web.Response(text="Hello ")

        def middleware_factory(text):
            @web.middleware
            async def sample_middleware(request, handler):
                resp = await handler(request)
                resp.text = resp.text + text
                return resp
            return sample_middleware

        app = web.Application(middlewares=[middleware_factory("test factory")])
        app.router.add_get('/', test)
        client = await aiohttp_client(app)
        resp = await client.get("/")
        assert resp.status == 200
        assert await resp.text() == "Hello test factory"

    @pytest.mark.asyncio
    async def test_cleanap_context(self, aiohttp_client):
        #  данный механизм можно использовать для инициализиации
        #  и закрытия рерусров, это лучше чем сигналы on_startup
        #  and cleanup, т.к. если во время инициализации произойдет
        #  исключение, при завершении работы - корутина cleanup
        #  вызовется все равно, а здесь можно сделать генератор
        #  и все отработает корректно
        list_message: list[str] = []

        async def test(request):
            list_message.append("request_header")
            return web.Response(text="Hello ")

        async def pg_engine(app):
            # инициализация движка бд
            app['pg_engine'] = 1
            list_message.append("start")
            yield
            # завершение движка бд
            list_message.append("stop")
            app['pg_engine'] = 0

        app = web.Application()
        app.router.add_get('/', test)
        app.cleanup_ctx.append(pg_engine)
        client = await aiohttp_client(app)
        await client.get("/")
        await client.close()
        assert "start request_header stop".split() == list_message
