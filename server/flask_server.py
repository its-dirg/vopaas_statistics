from base64 import urlsafe_b64decode, urlsafe_b64encode
from importlib import import_module
import json
import logging
from flask.ext.babel import Babel
from flask.ext.mako import MakoTemplates, render_template
from flask.helpers import send_from_directory
from jwkest import BadSignature
from jwkest.jwk import rsa_load, RSAKey
from jwkest.jws import NoSuitableSigningKeys
from mako.lookup import TemplateLookup
from flask import Flask
from flask import abort
from flask import request
from flask import session
from flask import redirect

from urllib.parse import parse_qs
from vopaas_statistics.db import StatDatabase
from vopaas_statistics.exceptions import StatServiceTickerError
from vopaas_statistics.stat_service import StatService, JWTHandler

LOGGER = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
babel = Babel(app)


@babel.localeselector
def get_locale():
    try:
        return session["language"]
    except:
        return get_browser_lang()


@app.route("/static/<path:path>")
def get_static(path):
    return send_from_directory('', path)


def get_browser_lang():
    return request.accept_languages.best_match(['sv', 'en'])


def change_language():
    if "language" not in session:
        session["language"] = get_browser_lang()
    if ("lang" in request.form):
        session["language"] = request.form["lang"]
        return True
    return False


@app.route("/get_ticket", methods=['GET'])
def get_ticket():
    ticket = stat_service.create_ticket()
    return ticket, 200


@app.route("/register/<jwt>", methods=['POST'])
def register_call(jwt):
    # parsed_qs = parse_qs(request.query_string.decode())
    # jwt = None
    jso = None
    # try:
    #     jwt = parsed_qs["jwt"][0]
    # except KeyError:
    #     abort(400)
    try:
        jso = JWTHandler.unpack_jwt(jwt, keys)
    except BadSignature:
        LOGGER.error("Bad signature on jwt")
        abort(401)
    except NoSuitableSigningKeys:
        LOGGER.exception("No suitable signing keys")
        abort(500)

    if not jso:
        abort(400)

    try:
        stat_service.register_call(jso["sp"], jso["idp"], jso["ticket"])
    except StatServiceTickerError:
        abort(401)

    return "", 200


@app.route("/get_stat/<sp>")
def get_stat(sp):
    stat = stat_service.get_stat(sp)
    stat = json.dumps(stat)
    return stat, 200


@app.route("/get_all_sp")
def get_all_sp():
    all_sp = stat_service.get_all_sp()
    all_sp = json.dumps(all_sp)
    return all_sp, 200


@app.route("/", methods=["GET", "POST"])
def show_all_sp():
    change_language()
    sp_list = stat_service.get_all_sp()
    sp_and_url = []
    for sp in sp_list:
        sp_and_url.append((sp, urlsafe_b64encode(sp.encode()).decode()))


    return render_template('pick_sp.mako',
                           name="mako",
                           form_action='/',
                           sp_link_base="%s/statistics" % base,
                           sp_list=sp_and_url,
                           language=session["language"])


@app.route("/statistics/<sp>", methods=["GET", "POST"])
def show_stat(sp):
    change_language()
    decoded_sp = urlsafe_b64decode(sp.encode()).decode()
    stat = stat_service.get_stat(decoded_sp)
    return render_template('statistics.mako',
                           name="mako",
                           form_action='/statistics/%s' % sp,
                           sp=decoded_sp,
                           stat=stat,
                           language=session["language"])

def import_database_class():
    db_module = app.config['DATABASE_CLASS_PATH']
    path, _class = db_module.rsplit('.', 1)
    module = import_module(path)
    database_class = getattr(module, _class)
    return database_class

class MustInheritFromStatdatabase(Exception):
    pass

if __name__ == "__main__":
    import ssl

    app.config.from_pyfile("settings.cfg")
    LOGGER = logging.getLogger("alservice")
    hdlr = logging.FileHandler(app.config["LOG_FILE"])
    base_formatter = logging.Formatter("[%(asctime)-19.19s] [%(levelname)-5.5s]: %(message)s")
    hdlr.setLevel(app.config["LOG_LEVEL"])
    hdlr.setFormatter(base_formatter)
    LOGGER.addHandler(hdlr)
    LOGGER.setLevel(logging.DEBUG)
    mako = MakoTemplates()
    mako.init_app(app)
    app._mako_lookup = TemplateLookup(directories=["templates"],
                                      input_encoding='utf-8', output_encoding='utf-8',
                                      imports=["from flask.ext.babel import gettext as _"])
    context = None
    if app.config['SSL']:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.load_cert_chain(app.config["SERVER_CERT"], app.config["SERVER_KEY"])
    global keys
    global stat_service
    global base
    keys = []
    for key in app.config["JWT_PUB_KEY"]:
        _bkey = rsa_load(key)
        pub_key = RSAKey().load_key(_bkey)
        keys.append(pub_key)
    # salt = app.config["SALT"]

    # message = open(app.config["MESSAGE_TEMPLATE"], "r").read()
    # message_from = app.config["MESSAGE_FROM"]
    # message_subject = app.config["MESSAGE_SUBJECT"]
    # smtp_server = app.config["SMTP_SERVER"]

    # verify_url = "%s://%s:%s/verify_token" % ("https" if context else "http",
    #                                           app.config['HOST'],
    #                                           app.config['PORT'])

    base = "%s://%s:%s" % ("https" if context else "http", app.config['HOST'], app.config['PORT'])

    database_class = import_database_class()
    if not issubclass(database_class, StatDatabase):
        raise MustInheritFromStatdatabase("%s does not inherit from StatDatabase" % database_class)
    database = database_class(*app.config['DATABASE_CLASS_PARAMETERS'])

    stat_service = StatService(database)
    
    app.secret_key = app.config['SECRET_SESSION_KEY']
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'],
            ssl_context=context)
