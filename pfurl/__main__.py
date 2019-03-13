import os
import aiopg
import aiohttp
import aiohttp_jinja2
import asyncio
import jinja2
import logging
# import requests  # use if using api to store in /up
from short import generate_hash
from urllib.parse import urlparse


async def connect_db():
    address = os.environ.get(
        'POSTGRES_ADDRESS',
        'localhost:5432'
    )
    username = os.environ.get(
        'POSTGRES_USERNAME',
        'pfurl'
    )
    password = os.environ.get(
        'POSTGRES_PASSWORD',
        'pfurl'
    )
    database = os.environ.get(
        'POSTGRES_DATABASE',
        'pfurl'
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


async def index_get(request):
    context = {}
    return aiohttp_jinja2.render_template(
        'index.html',
        request,
        context
    )


async def index_post(request):
    data = await request.json()

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

        return aiohttp.web.json_response(context['newurl'].strip('"'))


@aiohttp_jinja2.template('base.html')
async def up_index(request):
    context = {}

    if request.method == 'GET':
        return aiohttp_jinja2.render_template(
            'form.html',
            request,
            context
        )

    data = await request.post()

    if await validate_url(data['url']) is not False:
        """ Using api method """
        """
        url = 'http://pfurl.me/'
        headers = {'Content-Type': 'application/json'}

        payload = {'url': data['url']}

        response = requests.post(url, headers=headers, json=payload)
        print(response)
        body = response.json()
        context = {
            'url': data['url'],
            'newurl': body['url']
        }
        """
        """ Generating hash method """

        ghash = generate_hash()
        newurl = 'http://pfurl.me/' + ghash
        context = {
            'url': data['url'],
            'newurl': newurl
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
    statement = 'select url from urls where hash=%s'
    hash = request.match_info.get('hash')
    ret = []
    
    async with request.app['pool'].acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                statement,
                (hash,)
            )
            async for row in cursor:
                ret.append(row)

    return aiohttp.web.HTTPFound(ret[0])


async def http_handler():
    pool = await connect_db()
    print('Connected to postgresql!')

    app = aiohttp.web.Application()
    app.router.add_route('GET', '/', index_get)
    app.router.add_route('POST', '/', index_post)
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

    site = aiohttp.web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()

    print('Serving on http://localhost:80/')


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
