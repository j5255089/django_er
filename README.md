# django_mysql_comment
auto add comment for mysql table and column

the property ```verbose_name``` of the django model will be used as ```comment``` for mysql table

## How to use

the model 
```
name = models.CharField(max_length=200, verbose_name="名称", blank=True, default=None)
age = models.SmallIntegerField(verbose_name="年龄", blank=True, default=None)
```

then, install the package
```
pip install addcomments
```

in ```settings.py``` add app
```
INSTALLED_APPS += [
    'addcomments',
]
```

next, type command
```
python manage.py addcolumncomments
```

finally, the info will be printed, all the models created will be processed
```
-- FOR test_student.name 
        ALTER TABLE test_student
        MODIFY COLUMN `name` varchar(200) COLLATE utf8mb4_bin NOT NULL  COMMENT '名称'
-- FOR test_student.age 
        ALTER TABLE test_student
        MODIFY COLUMN `age` smallint(6) NOT NULL  COMMENT '年龄'
```

## If any bug
you can fix by yourself or commit your issue here, I will fix

## TODO

- check if postgresql is okay