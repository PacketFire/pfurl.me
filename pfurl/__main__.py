from flask import Flask, render_template, request, redirect
from short import generate_hash
import re
import psycopg2


app = Flask(__name__)

regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])'
        r'?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


conn = psycopg2.connect(
    'postgresql://pfurl:pfurl@localhost:15432/pfurl'
)
db = conn.cursor()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')

        if re.match(regex, url):
            ghash = generate_hash()
            newurl = 'http://pfurl.me/' + ghash

            results = {
                "url": url,
                "newurl": newurl
            }

            statement = '''
            insert into pfurl (url, hash, newurl)
            values(%s, %s, %s);
            '''
            db.execute(
                statement,
                (
                    results['url'],
                    ghash,
                    results['newurl']
                )
            )
            conn.commit()

            return render_template('result.html', results=results)
        else:
            return render_template(
                'error.html',
                error="Input must contain valid url"
            )
    else:
        return render_template('form.html')


@app.route('/<hash>', methods=['GET', 'POST'])
def hash_redirect(hash):
    statement = 'select url from pfurl where hash=%s'
    db.execute(statement, (hash,))
    row = db.fetchone()
    conn.close()
    return redirect(row[0])


if __name__ == "__main__":
    app.run(port=80)
