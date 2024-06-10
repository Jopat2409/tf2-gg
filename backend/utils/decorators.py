from sqlalchemy import func, event

def __generate_id_factory(cls, id_col):
    def next_id():
        if cls.UNCOMMITTED_IDS:
            new_id = max(cls.UNCOMMITTED_IDS) + 1
        else:
            new_id = int(cls.query.with_entities(func.max(getattr(cls,id_col))).first()[0] or 0) + 1
        cls.UNCOMMITTED_IDS.add(new_id)
        return new_id
    return next_id

def __clear_id_factory(cls):
    def clear_ids(mapper, connection, target):
        to_clear = []
        for id_ in cls.UNCOMMITTED_IDS:
            if cls.get(id_):
                to_clear.append(id_)
        for id_ in to_clear:
            cls.UNCOMMITTED_IDS.remove(id_)
    return clear_ids

def cache_ids(id_col):
    """
    Decorator used to autogenerate cache autoincrememnted IDs that have not yet been committed to the database

    Implements two static functions into a database model: \n
        `get_next_id` which generates the next ID to be used based on the IDs currently in the database and the uncommitted IDs\n
        `discard_committed_ids` which is called whenever a class of this type is inserted into the database. Removes all
        committed IDs from the set
    """
    def decorator(cls):
        cls.UNCOMMITTED_IDS = set()
        cls.discard_committed_ids = staticmethod(__clear_id_factory(cls))
        cls.get_next_id = staticmethod(__generate_id_factory(cls, id_col))
        event.listen(cls, "after_insert", cls.discard_committed_ids)
        return cls
    return decorator
