# 构建包
```python setup.py sdist bdist_wheel```

# 上传包
```twine upload ./dist/*```

输入用户名:smjkzsl
输入密码:*****

## 生成全局环境 requirement.txt

```pip install pipreqs```

而后运行:
```pipreqs . --encoding=utf8 --force```