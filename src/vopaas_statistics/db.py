import hashlib
import logging
from abc import abstractmethod
import dataset
from datetime import datetime

__author__ = 'mathiashedstrom'

LOGGER = logging.getLogger(__name__)


class StatDatabase(object):
    SP = "sp"
    IDP = "idp"
    TICKET = "ticket"

    @staticmethod
    def validation(attributes: dict):
        validation_message = ""
        if attributes is not None:
            for attr in attributes:
                if not isinstance(attributes[attr], str):
                    validation_message += "The value for %s is not allowed to be empty." % attr

                elif attributes[attr] is None or len(attributes[attr]) <= 0:
                    validation_message += "The type of %s must be string." % attr
        if len(validation_message) > 0:
            LOGGER.error("Attributes cannot be saved to the database since they are invalid. %s",
                         validation_message)
            raise Exception(validation_message)

    @abstractmethod
    def save_ticket(self, ticket):
        StatDatabase.validation(
            {
                StatDatabase.TICKET: ticket,
            }
        )

    @abstractmethod
    def remove_ticket(self, ticket):
        StatDatabase.validation(
            {
                StatDatabase.TICKET: ticket,
            }
        )

    @abstractmethod
    def register_call(self, sp: str, idp: str):
        StatDatabase.validation(
            {
                StatDatabase.SP: sp,
                StatDatabase.IDP: idp
            }
        )

    @abstractmethod
    def get_stat(self, sp: str):
        StatDatabase.validation(
            {
                StatDatabase.SP: sp
            }
        )

    def get_all_sp(self):
        raise NotImplementedError()


class StatSQLiteDatabase(StatDatabase):
    STAT_TABLE_NAME = "statistic_table"
    IDP_TABLE_NAME = "idp_table"
    SP_TABLE_NAME = "sp_table"
    TICKET_TABLE_NAME = "ticket_table"

    SP_NAME = "sp_name"

    IDP_NAME = "idp_name"

    TICKET_TICKET_PRIMARY = "ticket"
    TICKET_TIMESTAMP = "time_stamp"

    # TODO How do you use composite and foreign keys with dataset?
    STAT_PRIMARY = "sp_idp_pair"
    STAT_SP_ID = "sp_id"
    STAT_IDP_ID = "idp_id"
    STAT_FREQUENCY = "frequency"

    @staticmethod
    def create_key(sp: str, idp: str):
        return hashlib.sha224((sp + idp).encode("UTF-8")).hexdigest()

    def __init__(self, database_path=None):
        self.c_db = dataset.connect('sqlite:///:memory:')
        if database_path:
            self.c_db = dataset.connect('sqlite:///' + database_path)

        self.sp_table = self.c_db.get_table(
            StatSQLiteDatabase.SP_TABLE_NAME,
        )

        self.idp_table = self.c_db.get_table(
            StatSQLiteDatabase.IDP_TABLE_NAME,
        )

        self.stat_table = self.c_db.get_table(
            StatSQLiteDatabase.STAT_TABLE_NAME,
            primary_id=StatSQLiteDatabase.STAT_PRIMARY,
            primary_type='String(250)'
        )

        self.ticket_table = self.c_db.get_table(
            StatSQLiteDatabase.TICKET_TABLE_NAME,
            primary_id=StatSQLiteDatabase.TICKET_TICKET_PRIMARY,
            primary_type='String(250)'
        )
        
    def save_ticket(self, ticket):
        data = {
            StatSQLiteDatabase.TICKET_TICKET_PRIMARY: ticket,
            StatSQLiteDatabase.TICKET_TIMESTAMP: datetime.now()
        }
        self.ticket_table.insert(data)

    def remove_ticket(self, ticket):
        super(StatSQLiteDatabase, self).remove_ticket(ticket)
        try:
            search = {StatSQLiteDatabase.TICKET_TICKET_PRIMARY: ticket}
            self.ticket_table.delete(**search)
            return True
        except:
            pass
        return False

    def register_call(self, sp: str, idp: str):
        super(StatSQLiteDatabase, self).register_call(sp, idp)

        key = StatSQLiteDatabase.create_key(sp, idp)
        search = {StatSQLiteDatabase.STAT_PRIMARY: key}
        row = self.stat_table.find_one(**search)

        if not row:
            _sp = {StatSQLiteDatabase.SP_NAME: sp}
            sp_row = self.sp_table.find_one(**_sp)
            if not sp_row:
                sp_id = self.sp_table.insert(_sp)
            else:
                sp_id = sp_row["id"]

            _idp = {StatSQLiteDatabase.IDP_NAME: idp}
            idp_row = self.idp_table.find_one(**_idp)
            if not idp_row:
                idp_id = self.idp_table.insert(_idp)
            else:
                idp_id = idp_row["id"]

            _stat = {
                StatSQLiteDatabase.STAT_PRIMARY: key,
                StatSQLiteDatabase.STAT_SP_ID: sp_id,
                StatSQLiteDatabase.STAT_IDP_ID: idp_id,
                StatSQLiteDatabase.STAT_FREQUENCY: 1,
            }

            self.stat_table.insert(_stat)
        else:
            update = {
                StatSQLiteDatabase.STAT_PRIMARY: row[StatSQLiteDatabase.STAT_PRIMARY],
                StatSQLiteDatabase.STAT_FREQUENCY: row[StatSQLiteDatabase.STAT_FREQUENCY] + 1
            }
            self.stat_table.update(update, [StatSQLiteDatabase.STAT_PRIMARY])

    def get_stat(self, sp):
        super(StatSQLiteDatabase, self).get_stat(sp)

        sp_search = {StatSQLiteDatabase.SP_NAME: sp}
        sp_row = self.sp_table.find_one(**sp_search)
        if not sp_row:
            return []
        sp_id = sp_row["id"]

        db_query = "SELECT {stat_table}.{frequency}, {idp_table}.{idp_name} " \
                   "FROM {stat_table} " \
                   "INNER JOIN {idp_table} " \
                   "ON {stat_table}.{idp_id}={idp_table}.id " \
                   "WHERE {stat_table}.{sp_id}={search_sp} " \
                   "ORDER BY {stat_table}.{frequency} DESC"
        db_query = db_query.format(stat_table=StatSQLiteDatabase.STAT_TABLE_NAME,
                                   frequency=StatSQLiteDatabase.STAT_FREQUENCY,
                                   idp_id=StatSQLiteDatabase.STAT_IDP_ID,
                                   sp_id=StatSQLiteDatabase.STAT_SP_ID,
                                   idp_table=StatSQLiteDatabase.IDP_TABLE_NAME,
                                   idp_name=StatSQLiteDatabase.IDP_NAME,
                                   search_sp=sp_id)

        rows = self.c_db.query(db_query)
        result = []
        for row in rows:
            result.append(
                (row[StatSQLiteDatabase.IDP_NAME], row[StatSQLiteDatabase.STAT_FREQUENCY]))
        return result

    def get_all_sp(self):
        all_rows = self.sp_table.all()
        all_sp = []
        for row in all_rows:
            all_sp.append(row[StatSQLiteDatabase.SP_NAME])
        return all_sp
