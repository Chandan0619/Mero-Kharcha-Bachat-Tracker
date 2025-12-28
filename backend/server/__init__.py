import pymysql

# This tricks Django into thinking pymysql is a newer mysqlclient version
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

