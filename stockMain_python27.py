# encoding=utf-8
import requests
import matplotlib.pyplot as plt
import math
from sklearn import tree
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier(n_estimators=8)
import random

print "please input the stock code:"
stock_code = input()
stock_code = str(stock_code)
# 这是对一个股进行分析的代码
r = requests.get('http://q.stock.sohu.com/hisHq?'
                 '&code=cn_' + stock_code +
                 '&start=20000501'
                 '&end=20181010'
                 '&stat=1&order=D&period=d&callback=historySearchHandler&rt=jsonp')
content = r.content
# 得到的json里有中文，需要解码:gbk->unicode(python默认编码格式)->utf-8
content = content.decode("gbk").encode('utf-8')
if "non-existent" in content:
    print "The stock code you input does not exist!"
    input()
    exit()
pos_begin = content.find('[[')
pos_end = content.find(']]')
content = content[pos_begin+2:pos_end]
# 把整条信息分割成 每个工作日 的信息，存到一个列表中
content = content.split('],[')
# 开始逐条处理 每个工作日 的信息,处理后的信息存入列表result。每日涨跌幅信息另存入列表up_down_list
# [日期，开盘价，收盘价，涨跌额，涨跌幅，最低，最高，成交量，成交额，换手率]
result = []
up_down_list = []
print "[date  Change]"
for d in content:
    # 去掉开头结尾的无用引号，并分割成每一项：
    # [日期，开盘价，收盘价，涨跌额，涨跌幅，最低，最高，成交量，成交额，换手率]
    d = d[1:-1]
    d = d.split('","')
    # 第一项外所有项转为数字，日期、成交量为整型，其余为浮点型且'%'需要专门处理
    for i_int in [7]:
        d[i_int] = int(d[i_int])
    for i_float in [1, 2, 3, 5, 6, 8]:
        d[i_float] = float(d[i_float])
    for i_f_percent in [4, 9]:
        d[i_f_percent] = float(d[i_f_percent][0:-1]) * 0.01
    result.append(d)
    up_down_list.append(d[4])
# 注意翻转，此时是日期从后往前排的，需要翻转成日期从前往后排的
up_down_list.reverse()
result.reverse()
for d in result:
    print d[0], " ", d[4]*100, "%"
print "From", result[0][0], "to", result[-1][0], "totally", len(result), "days' stock history has been gathered, now analysing......"
# 至此，列表result里已存入整理完毕的每日股票数据，一维列表up_down_list已存入每日涨跌幅信息。
# 开始构建sklearn格式的训练集。根据过去20天的涨跌幅预测明天的涨跌幅。明天的涨跌幅分为22档（22个标签）
# 低于-5%一个标签，高于5%一个标签。然后每0.5%分一个标签，且。因此，可以用“*1000，小数部分四舍五入即round函数，取整，/5，+1或者-1”的方法得到标签
# 每天的标签存入列表labels_everyday
labels_everyday = []
for i in up_down_list:
    i = i * 1000
    i = round(i)
    i = int(i)
    i = i / 5
    if i != 0:
        if i > 0:
            i = i + 1
        else:
            i = i - 1
    if i > 10:
        i = 11
    if i < -10:
        i = -11
    labels_everyday.append(i)
# 前20天的标签用不到，为了和features_all保持一致，去掉前20天的标签。使得labels_everyday从“第21天的标签”开始。
labels_everyday = labels_everyday[20:]
# 画图展示一下所有天的涨跌幅
plt.title("Stock History Show")
plt.bar(range(len(labels_everyday)), labels_everyday)
plt.show()
# features_all是“每20天作为一组特征”，所有组特征都保存在这里。注意features_all是从“第21天的前20天”开始的。
# 也就是说，features_all和labels_everyday是彼此配对的，同样的下标对应了同样的“特征（20维）配标签”。
features_all = []
for i in range(len(up_down_list)-20):
    X_item = []
    for j in range(20):
        X_item.append(up_down_list[i+j])
    features_all.append(X_item)
# 开始构建训练集和测试集。训练集占70%的数据，测试集30%。整个数据集随机分割。
# 构建训练集部分：X配y。以及测试集部分：x_t配y_t。
x = []
y = []
x_t = []
y_t = []
# 挑选训练集数据序号，占据70%。
train_No = random.sample(range(0, len(labels_everyday)), int(0.9 * len(labels_everyday)))
for i in range(0, len(features_all)):
    if i in train_No:
        x.append(features_all[i])
        y.append(labels_everyday[i])
    else:
        x_t.append(features_all[i])
        y_t.append(labels_everyday[i])
# x,y,x_t,y_t全部构建完毕。

# 开始训练
clf.fit(x, y)

# 开始用测试集测定训练效果
predict_t = clf.predict(x_t)
total_count = 0
right_count = 0
for i in range(len(predict_t)):
    print "predict:", predict_t[i], "  fact:", y_t[i]
    flag = predict_t[i] * y_t[i]
    total_count += 1
    if flag >= 0:
        right_count += 1
print "---Accuracy Analyse Result---"
print "Total:", total_count
print "Right:", right_count
print "Correct Rate:", right_count * 1.0 / total_count

# 展示最近20天的涨跌情况
plt.title("Latest 20 Days")
plt.bar(range(len(up_down_list[len(up_down_list)-20:])), up_down_list[len(up_down_list)-20:])
plt.show()
# 预测明天的涨跌幅
pre = clf.predict([features_all[-1]])
pre_1 = pre[0] * 0.5
print "---Prediction Tomorrow---"
print "Prediction: the Change tomorrow is likely to be:",
if pre_1 > 0:
    print "+",
print pre_1, "%  ",
print "(Stock Code: ", stock_code, ")"

input()
