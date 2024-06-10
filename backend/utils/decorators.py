from sqlalchemy import func, event

def __generate_id_factory(cls, id_col):
    def next_id():
        lower_bound = max(cls.UNCOMMITTED_IDS) + 1 if cls.UNCOMMITTED_IDS else 1
        upper_bound = int(cls.query.with_entities(func.max(getattr(cls,id_col))).first()[0] or 0) + 1
        new_id = max(lower_bound, upper_bound)
        cls.UNCOMMITTED_IDS.add(new_id)
        return new_id
    return next_id

""" def __clear_id_factory(cls):
    def clear_ids(mapper, connection, target):
        to_clear = []
        for id_ in cls.UNCOMMITTED_IDS:
            if cls.get(id_):
                to_clear.append(id_)
        for id_ in to_clear:
            cls.UNCOMMITTED_IDS.remove(id_)
    return clear_ids """

def __clear_out_of_scope(cls, id_col):
    def clear_out_of_scope(self):
        id_ = getattr(self, id_col)
        cls.UNCOMMITTED_IDS.discard(id_)
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
        cls.UNCOMMITTED_IDS = set()
        #cls.discard_committed_ids = staticmethod(__clear_id_factory(cls))
        cls.get_next_id = staticmethod(__generate_id_factory(cls, id_col))
        cls.__del__ = __clear_out_of_scope(cls, id_col)
        #event.listen(cls, "after_insert", cls.discard_committed_ids)
        return cls
    return decorator
