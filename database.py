from sqlite3 import connect
import pandas as pd
from settings import config as conf
from itertools import zip_longest
from os import path
import base64

class db(object):
    def __init__(self, base) -> None:
        if base.endswith('.db'):
            self.con = connect(base, check_same_thread=False)
        else:
            self.con = connect(f'{base}.db', check_same_thread=False)
        self.cur = self.con.cursor()
        self.conf = conf()

    def returnAnswer(self, answer):
        if len(answer) == 0:
            return answer
        if len(answer) == 1:
                if len(answer[0]) == 1:
                    return answer[0][0]
                else:
                    return answer[0]
        else:
            if len(answer[0]) == 1:
                return [_[0] for _ in answer]
            else:
                return answer

    def action(self, command: str, table: str = conf().defaultTableName, config: str = None):
        if command == 'create':
            self.cur.execute(f'{self.conf.DDL[command]} TABLE IF NOT EXISTS {table} ({config})')
        elif command == 'alter':
            self.cur.execute(f'{self.conf.DDL[command]} TABLE IF EXISTS {table}{config}')
        elif command == 'drop':
            self.cur.execute(f'{self.conf.DDL[command]} TABLE IF EXISTS {table}')
        elif command == 'insert':
            count = len(self.cur.execute(f'{self.conf.DML["select"]} * FROM {table}').description)
            # values = config.split(self.conf.insertSplit)
            values = config
            [values.__setitem__(i, None) for i, value in enumerate(values) if value == 'None']
            self.cur.executemany(f'{self.conf.DML[command]} INTO {table} VALUES ({", ".join(["?"]*count)})', list(zip_longest(*[iter(values)]*count)))
            self.con.commit()
        # elif command == 'insert item':
        #     configSplit = config.split(self.conf.insertSplit)
        #     if len(configSplit) == 2 and not '' in configSplit and not ' ' in configSplit:
        #         item, data = configSplit
        #         self.cur.execute(f'{self.conf.DML["insert"]} INTO {table} ({item}) VALUES (?)', (data, ))
        #         self.con.commit()
        elif command == 'update':
            configSplit = config.split(self.conf.updateSplit)
            if len(configSplit) == 2 and not '' in configSplit and not ' ' in configSplit:
                expression, conditions = configSplit
                self.cur.execute(f'{self.conf.DML[command]} {table} SET {expression} WHERE {conditions}')
                self.con.commit()
            else:
                print('er')
        elif command == 'update item':
            # configSplit = config.split(self.conf.updateSplit)
            # if len(configSplit) == 2 and not '' in configSplit and not ' ' in configSplit:
            #     expression, conditions = configSplit
                self.cur.execute(f'{self.conf.DML["update"]} {table} SET img = :img WHERE {config["WHERE"]}', config)
                self.con.commit()
            # else:
            #     print('er')
        elif command == 'delete':
            self.cur.execute(f'{self.conf.DML[command]} FROM {table} WHERE {config}')
            self.con.commit()
        elif command == 'find':
            configSplit = config.split(self.conf.findSplit)
            if len(configSplit) == 2 and not '' in configSplit and not ' ' in configSplit:
                expressions, conditions = configSplit
                self.cur.execute(f'{self.conf.DML["select"]} {expressions} FROM {table} WHERE {conditions}')
            else:
                return None
            answer = self.cur.fetchall()
            return self.returnAnswer(answer)
        elif command == 'sort':
            configSplit = config.split(self.conf.sortSplit)
            if len(configSplit) == 3 and not '' in configSplit and not ' ' in configSplit:
                expressions, conditions, expression = configSplit
                self.cur.execute(f'{self.conf.DML["select"]} {expressions} FROM {table} WHERE {conditions} ORDER BY {expression}')
            elif len(configSplit) == 4 and not '' in configSplit and not ' ' in configSplit:
                expressions, conditions, expression, numberRows = config.split(self.conf.sortSplit)
                self.cur.execute(f'{self.conf.DML["select"]} {expressions} FROM {table} WHERE {conditions} ORDER BY {expression} LIMIT {numberRows}')
            elif len(configSplit) == 5 and not '' in configSplit and not ' ' in configSplit:
                expressions, conditions, expression, numberRows, offsetValue = config.split(self.conf.sortSplit)
                self.cur.execute(f'{self.conf.DML["select"]} {expressions} FROM {table} WHERE {conditions} ORDER BY {expression} LIMIT {numberRows} OFFSET {offsetValue}')
            else:
                return None
            # ASC, DESC
            answer = self.cur.fetchall()
            if len(answer) == 1:
                return answer[0]
            else:
                return answer
        elif command == 'show':
            answer = self.cur.fetchall()
            if len(answer) == 1:
                return answer[0]
            else:
                return answer
        else:
            self.cur.execute(command)
            self.con.commit()

    def convert(self, table: str = conf().defaultTableName, outFormat: str = conf().defaultConvertFormat, savePath: str = 'out', query: str = None, **config):
        query = f'SELECT * FROM {table}' if query == None else query.replace('table', table)
        savePath, ext = path.splitext(savePath)
        if outFormat == 'pickle':
            pd.read_sql_query(query, self.con).to_pickle(path=savePath, **config)
        if outFormat == 'csv':
            pd.read_sql_query(query, self.con).to_csv(path_or_buf=f'{savePath}.csv', **config)
        if outFormat == 'hdf':
            pd.read_sql_query(query, self.con).to_hdf(path_or_buf=f'{savePath}.hdf', **config)
        if outFormat == 'dict':
#           dict: dict like {column -> {index -> value}}
#           list: dict like {column -> [values]}
#           series: dict like {column -> Series(values)}
#           split: dict like {'index' -> [index], 'columns' -> [columns], 'data' -> [values]}
#           tight: dict like {'index' -> [index], 'columns' -> [columns], 'data' -> [values], 'index_names' -> [index.names], 'column_names' -> [column.names]}
#           records: list like [{column -> value}, … , {column -> value}]
#           index: dict like {index -> {column -> value}}
            return pd.read_sql_query(query, self.con).to_dict(**config)
        if outFormat == 'excel':
            pd.read_sql_query(query, self.con).to_excel(excel_writer=f'{savePath}.xlsx', **config)
        if outFormat == 'json':
            pd.read_sql_query(query, self.con).to_json(path_or_buf=f'{savePath}.json', **config)
        if outFormat == 'html':
            return pd.read_sql_query(query, self.con).to_html(**config)
        if outFormat == 'string':
            return pd.read_sql_query(query, self.con).to_string(**config)
        if outFormat == 'clipboard':
            pd.read_sql_query(query, self.con).to_clipboard(**config)
        if outFormat == 'markdown':
            return pd.read_sql_query(query, self.con).to_markdown(**config)

    def tableColumns(self, table: str = conf().defaultTableName):
        return [_[0] for _ in self.cur.execute(f'{self.conf.DML["select"]} * FROM {table}').description]

    def disconnect(self):
        self.cur.close()

# print(db('tutorial').convert(outFormat='markdown',))
# print(db('tutorial').tableColumns())