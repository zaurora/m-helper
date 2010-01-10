#!/usr/bin/env python

import sys, glob, re
import MySQLdb, sqlparse

conn = MySQLdb.connect(user = "mangos", passwd = "mangos")

# Get the database versions
version = { "realmd": "realmd_db_version", "characters": "character_db_version", "mangos": "db_version" }
for db in version.keys():
    conn.query("SHOW COLUMNS FROM %s IN %s LIKE 'required_%%'" % (version[db], db))
    result = conn.store_result().fetch_row()
    version[db] = int(re.match("required_(\d+)_.*", result[0][0]).group(1))


# List all update scripts and extract the version and database they apply to
prog = re.compile(".*/(\d+)_(\d+)_([a-z]+)_?(\w*)\.sql")
def parse(name):
    res = prog.match(name)
    if not res:
        print("failed to parse "+name)
        sys.exit(-1)
    return ( name, ) + res.groups()

list = [parse(name) for name in glob.glob(sys.argv[1]+"/share/mangos/sql/updates/*.sql")]
list.sort(lambda x,y: int(x[1]) == int(y[1]) and int(x[2]) - int(y[2]) or int(x[1]) - int(y[1]))


# Go through all update scripts and apply those which are needed
for entry in list:
    if int(entry[1]) <= version[entry[3]]:
        continue

    print("Applying %s.%s (%s) to %s" % (entry[1], entry[2], entry[4], entry[3]))
    cursor = conn.cursor()
    cursor.execute("USE %s" % entry[3])

    script = open(entry[0]).read()
    for stmt in [stmt.strip() for stmt in sqlparse.split(script)]:
        if stmt:
            cursor.execute(stmt)

    cursor.execute("COMMIT")
    cursor.close()

conn.close()
