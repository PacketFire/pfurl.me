import os
import aiopg
import aiohttp
import aiohttp_jinja2
import asyncio
import jinja2
import logging
from short import generate_hash
from urllib.parse import urlparse


async def connect_db():
    address = os.environ.get(
        'POSTGRES_ADDRESS',
        'localhost:15432'
    )
    username = os.environ.get(
        'POSTGRES_USERNAME',
        'postgres'
    )
    password = os.environ.get(
        'POSTGRES_PASSWORD',
        'postgres'
    )
    database = os.environ.get(
        'POSTGRES_DATABASE',
        'apophis'
    )

    dsn = 'postgresql://{}:{}@{}/{}'.format(
        username,
        password,
        address,
        database
    )

    try:
        return await aiopg.create_pool(dsn)
    except Exception as e:
        logging.error(e)
        raise e


async def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


async def index(request):
    context = {}

    if request.method == 'GET':
        return aiohttp_jinja2.render_template(
            'index.html', 
            request, 
            context
        )
    
    data = await request.post()

    if await validate_url(data['url']) is not False:
        ghash = generate_hash()
        newurl = 'http://pfurl.me/' + ghash
        context = {
            "url": data['url'],
            "newurl": newurl
        }

        statement = '''
        insert into urls (url, hash, newurl)
        values(%s, %s, %s);
        '''

        async with request.app['pool'].acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    statement,
                    (
                        context['url'],
                        ghash,
                        context['newurl'],
                    )
                )
        
        return aiohttp.web.json_response(context['newurl'])


@aiohttp_jinja2.template('base.html')
async def up_index(request):
    if request.method == 'GET':
        context = {}
        return aiohttp_jinja2.render_template(
            'form.html',
            request,
            context
        )

    data = await request.post()
    print(data.url)

    if await validate_url(data['url']) is not False:
        ghash = generate_hash()
        newurl = 'http://pfurl.me/' + ghash
        context = {
            "url": data['url'],
            "newurl": newurl
        }

        statement = '''
        insert into pfurl (url, hash, newurl)
        values(%s, %s, %s);
        '''

        async with request.app['pool'].acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    statement,
                    (
                        context['url'],
                        ghash,
                        context['newurl'],
                    )
                )
        return aiohttp_jinja2.render_template(
            'result.html',
            request,
            context
        )

    context = {'error': 'Input must contain valid url'}
    return aiohttp_jinja2.render_template(
        'error.html',
        request,
        context
    )


async def hash_redirect(request):
    statement = 'select url from pfurl where hash=%s'
    hash = request.match_info.get('hash')

    async with request.app['pool'].acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                statement,
                (hash,)
            )
            ret = []
            async for row in cursor:
                ret.append(row)

    return aiohttp.web.HTTPFound(row[0])


async def http_handler():
    pool = await connect_db()
    print('Connected to postgresql!')

    app = aiohttp.web.Application()
    app.router.add_route('*', '/', index)
    app.router.add_route('*', '/up', up_index)
    app.router.add_route('GET', '/{hash}', hash_redirect)
    app.router.add_static('/pfurl/static', 'pfurl/static')
    app['pool'] = pool

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader('pfurl/templates')
    )

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()

    site = aiohttp.web.TCPSite(runner, '127.0.0.1', 8080)
    await site.start()

    print('Serving on http://127.0.0.1:8080/')


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(http_handler())
        loop.run_forever()
    except KeyboardInterrupt:
        logging.debug('Exiting, caught keyboard interrupt.')
        os._exit(0)
    except Exception as e:
        logging.error(e)
    finally:
        loop.close()
