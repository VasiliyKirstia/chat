class ResearchWorkRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'research_work':
            return 'research_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'research_work':
            return 'research_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'research_work' and obj2._meta.app_label == 'research_work':
           return True
        return None

    def allow_migrate(self, db, model):
        if db == 'research_db':
            return model._meta.app_label == 'research_work'
        elif model._meta.app_label == 'research_work':
            return False
        return None


class MainDataBaseRouter(object):
    def db_for_read(self, model, **hints):
        return 'default'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == 'default' and obj2._state.db == 'default':
            return True
        return None

    def allow_migrate(self, db, model):
        return True