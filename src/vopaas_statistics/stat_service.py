from base64 import urlsafe_b64encode
import hashlib
import random
from time import mktime, gmtime
from uuid import uuid4
from jwkest import jws
from jwkest.jwt import JWT
from vopaas_statistics.db import StatDatabase
from vopaas_statistics.exceptions import StatServiceTickerError


class JWTHandler(object):
    """
    Handles jwt
    """
    @staticmethod
    def _verify_jwt(jwt: str, keys: list):
        """
        Verify teh signature of the jwt
        :type keys: list[str]
        :param jwt: A signed jwt
        :param keys: A list of keys to use when verifying the signature
        """
        _jw = jws.factory(jwt)
        _jw.verify_compact(jwt, keys)

    @staticmethod
    def unpack_jwt(jwt: str, keys: list):
        """
        Unpacks a signed jwt question
        :type keys: list[str]
        :rtype: dict[str, str]
        :param jwt: A signed jwt containing the question (the idp, id and redirect_endpoint)
        :param keys: A list of keys to use when verifying the signature
        :return: The unpacked jwt
        """
        JWTHandler._verify_jwt(jwt, keys)
        _jwt = JWT().unpack(jwt)
        jso = _jwt.payload()
        if "sp" not in jso or "idp" not in jso or "ticket" not in jso:
            return None
        return jso
    
class StatService(object):

    def __init__(self, db: StatDatabase):
        self.db = db

    @staticmethod
    def _create_token(value: str):
        """
        Create a hashed, urlsafe, token. The hash is also based on time and random number.
        :rtype: str

        :param value: token base
        :return: A token
        """
        token = urlsafe_b64encode(
            hashlib.sha512((value + str(mktime(gmtime())) + str(random.getrandbits(1024)))
                           .encode()).hexdigest().encode()).decode()
        return token

    def create_ticket(self):
        ticket = StatService._create_token(uuid4().urn)
        self.db.save_ticket(ticket)
        return ticket

    def register_call(self, sp, idp, ticket):
        if self.db.remove_ticket(ticket):
            self.db.register_call(sp, idp)
        else:
            raise StatServiceTickerError("Not a valid ticket!")

    def get_stat(self, sp):
        return self.db.get_stat(sp)

    def get_all_sp(self):
        return self.db.get_all_sp()
