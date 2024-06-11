from src.app.models.home import HomeModel
from src.app.exceptions import GUIError
from src.dbservice import BaseDatabase


class Model:
    """Top level model of the MVC pattern.
    
    Controls all models of the application.
    """

    def __init__(self):
        self.home = HomeModel()
        self.db: BaseDatabase | None = None

    def set_db(self, db: BaseDatabase):
        if BaseDatabase not in db.__mro__:
            raise GUIError('Database must extend BaseDatabase')
        self.db = db
