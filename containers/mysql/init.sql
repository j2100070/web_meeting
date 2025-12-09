-- MYSQL_USERに権限を付与
-- 今回はdjangoというユーザを指定
GRANT ALL PRIVILEGES ON *.* TO 'your_db_user'@'%';
FLUSH PRIVILEGES;
