import re
import os
import aiopg
import aiohttp
import aiohttp_jinja2
import asyncio
import jinja2
import logging
from short import generate_hash


# app = Flask(__name__)
regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])'
        r'?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


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


async def index(request):
    if request.method == 'POST':
        url = request.form.get('url')

        if re.match(regex, url):
            ghash = generate_hash()
            newurl = 'http://localhost:8080/' + ghash

            results = {
                "url": url,
                "newurl": newurl
            }

            statement = '''
            insert into pfurl (url, hash, newurl)
            values(%s, %s, %s);
            '''

            pool = await connect_db()
            async with pool.acquire() as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        statement,
                        (
                            results['url'],
                            ghash,
                            results['newurl'],
                        )
                    )
            return aiohttp_jinja2.render_template(
                'result.html',
                request,
                results
            )
        else:
            context = {'error:', 'input must contain valid url'}
            return aiohttp_jinja2.render_template(
                'error.html',
                request,
                context
            )


async def hash_redirect(request):
    statement = 'select url from pfurl where hash=%s'
    hash = request.match_info.get('hash')
    pool = await connect_db()
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                statement,
                (hash,)
            )
            ret = []
            async for row in cursor:
                ret.append(row)

    return aiohttp.web.HTTPFound(ret)


async def http_handler():
    app = aiohttp.web.Application()
    app.router.add_route('GET', '/', index)
    app.router.add_route('GET', '/{hash}', hash_redirect)

    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader('pfurl/templates')
    )

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()

    site = aiohttp.web.TCPSite(runner, '127.0.0.1', 8080)
    await site.start()

    print('Serving on http://127.0.0.1:8080/')


async def run_coroutines():
    colist = [http_handler()]
    return await asyncio.gather(*colist, return_exceptions=True)


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