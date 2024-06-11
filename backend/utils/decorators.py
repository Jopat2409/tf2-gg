from sqlalchemy import func, event
from utils.typing import SiteID, TfSource

def __generate_id_factory(cls, id_col):
    def next_id():
        print("generating gernetaote epic")
        lower_bound = max(cls._CACHEIDS_UNCOMMITTED_IDS) + 1 if cls._CACHEIDS_UNCOMMITTED_IDS else 1
        upper_bound = int(cls.query.with_entities(func.max(getattr(cls,id_col))).first()[0] or 0) + 1
        new_id = max(lower_bound, upper_bound)
        cls._CACHEIDS_UNCOMMITTED_IDS.add(new_id)
        return new_id
    return next_id

def __clear_id_factory(cls):
    def clear_ids(mapper, connection, target):
        print("Clearing clearing epic")
        to_check = cls._CACHEIDS_UNCOMMITTED_IDS.copy()
        for id_ in to_check:
            if cls.get(id_):
                cls._CACHEIDS_UNCOMMITTED_IDS.discard(id_)
    return clear_ids

def __clear_out_of_scope(cls, id_col):
    def clear_out_of_scope(self):
        print("Clearing epic epic")
        pk_ = getattr(self, id_col)
        cls._CACHEIDS_UNCOMMITTED_IDS.discard(pk_)
    return clear_out_of_scope

def cache_ids(id_col):
    """"
    Decorator used to autogenerate cache autoincrememnted IDs that have not yet been committed to the database

    params:
        id_col[str]: The column of the model that is the primary UUID

    Implements two static functions into a database model: \n
        `get_next_id` which generates the next ID to be used based on the IDs currently in the database and the uncommitted IDs\n
        `discard_committed_ids` which is called whenever a class of this type is inserted into the database. Removes all
        committed IDs from the set

    Classes that this function decorates MUST implement a `get(id)` method, which should return Nothing (or `false`) if there does not
    exist an isntance in the database with the id `id`, else `true`
    """
    def decorator(cls):
        cls._CACHEIDS_UNCOMMITTED_IDS = set()

        cls.discard_committed_ids = staticmethod(__clear_id_factory(cls))
        cls.get_next_id = staticmethod(__generate_id_factory(cls, id_col))
        event.listen(cls, "after_insert", cls.discard_committed_ids)
        return cls
    return decorator

def __set_id_factory(rgl, etf2l, ugc):
    def set_id(self, id_: SiteID):
        if id_.get_source() == TfSource.RGL:
            setattr(self, rgl, id_.get_id())
        elif id_.get_source() == TfSource.ETF2L:
            setattr(self, etf2l, id_.get_id())
        elif id_.get_source() == TfSource.UGC:
            setattr(self, ugc, id_.get_id())
    return set_id

def __get_id_factory(rgl, etf2l, ugc):
    def get_id(self) -> SiteID | None:
        if getattr(self, rgl) is not None:
            return SiteID.rgl_id(getattr(self, rgl))
        elif getattr(self, etf2l) is not None:
            return SiteID.etf2l_id(getattr(self, etf2l))
        elif getattr(self, ugc) is not None:
            return SiteID.etf2l_id(getattr(self, ugc))
        return SiteID.rgl_id(None)
    return get_id

def site_resource(rgl_col, etf2l_col, ugc_col):
    """
    Decorator used to mark models as being resources from TF2 endpoints

    Every site resource has three columns, one for the RGL id `rgl_col`, one for the ETF2L ID `etf2l_col`, and one for the UGC ID `ugc_col`

    This decorator also implements two methods to interact with these source IDs, `set_source_id(SiteID)`, and `get_source_id() -> SiteID`
    """
    def decorator(cls):
        cls.set_source_id = __set_id_factory(rgl_col, etf2l_col, ugc_col)
        cls.get_source_id = __get_id_factory(rgl_col, etf2l_col, ugc_col)
        return cls
    return decorator


def __stage_factory(cls, pk_col):
    def stage(self, session):
        pk_ = getattr(self, pk_col)
        if not cls.get(pk_) and pk_ not in cls._STAGEDMODEL_STAGED_OBJECTS:
            session.merge(self)
            cls._STAGEDMODEL_STAGED_OBJECTS.add(pk_)
    return stage

def __clear_staged_factory(cls):
    def clear(mapper, connection, target):
        to_check = cls._STAGEDMODEL_STAGED_OBJECTS.copy()
        for i in to_check:
            if cls.get(i):
                cls._STAGEDMODEL_STAGED_OBJECTS.discard(i)
    return clear

def __del_hook(cls, pk_col):
    def delete(self):
        cls._STAGEDMODEL_STAGED_OBJECTS.discard(getattr(self, pk_col))
    return delete

def staged_model(pk_col):
    def decorator(cls):
        cls._STAGEDMODEL_STAGED_OBJECTS = set()
        cls.stage = __stage_factory(cls, pk_col)
        cls.remove_committed_stages = staticmethod(__clear_staged_factory(cls))
        cls.__del__ = __del_hook(cls, pk_col)
        event.listen(cls, "after_insert", cls.remove_committed_stages)
        return cls
    return decorator
