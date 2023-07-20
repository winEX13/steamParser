from betterconf import field, Config
from default import default

de = default()

#-------------------------

de.DDL = {
    'create': 'CREATE',
    'alter': 'ALTER',
    'drop': 'DROP'
    }
de.DML = {
    'select': 'SELECT',
    'insert': 'INSERT',
    'update': 'UPDATE',
    'delete': 'DELETE'
}
de.DCL = {
    'grant': 'GRANT',
    'revoke': 'REVOKE'
}

de.defaultTableName = 'main'
de.defaultConvertFormat = 'excel'
de.insertSplit = ', '
de.updateSplit = '|sep|'
de.findSplit = '|'
de.sortSplit = '|'

de.version='1.0',

#-------------------------

class config(Config):
    pass

for key, value in de.items():
    setattr(config, key, field(key, default=value))

# print(config().site)
# print(config().site)