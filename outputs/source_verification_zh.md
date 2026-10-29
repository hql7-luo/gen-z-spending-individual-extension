# 财务数据来源与课程结果核验

核验日期：2026-10-28。核验对象：[Anand Kumar 发布的 Gen Z Money Spending Dataset](https://www.kaggle.com/datasets/manandkumar/gen-z-money-spending-dataset)，版本 1，文件 `genz_money_spends.csv`。

## 结论

字段、年龄范围、记录数、发布时间和两个核心结果均与课程报告一致。这是课程财务数据的高度一致恢复版本，可以继续原计划；由于当年原文件与代码已遗失，无法证明逐字节相同。不能确认这些记录是真实调查还是合成数据。

## 五项核验

| 核验项 | 实际证据 | 判断 |
| --- | --- | --- |
| 字段与取值 | 含收入、租金、杂货、外食、娱乐、订阅、教育、网购、储蓄、投资、旅行、健身、其他消费；年龄 18-27，收入 1,501-7,994 USD | 与报告第 7-8 页的财务数据描述，以及第 20-21 页图表字段和范围一致；报告并未展示逐行原始数值，不能逐行比对 |
| 数据规模 | 实际读取 1,700 行、15 列，15 列包括 ID 和 Age；没有缺失单元格、重复行、重复 ID 或非正收入 | 与报告中财务数据单独的规模一致。“1,700 条、15 字段”属于财务表，不是两份数据合计 |
| 两个核心指标 | Pearson r = 0.03008187006506225；消费超过收入者 860 / 1,700 = 50.588235294117645%；相等人数 0，排除人数 0 | 四舍五入分别为 0.03 和 50.6%，均匹配。SQLite 汇总计算与 Python 独立计算一致 |
| 发布时间 | 官方 API 记录版本 1 的 initial release 和最后更新时间均为 2025-01-31T12:27:43.5Z，只有一个发布版本 | 早于 2025 年 3 月。上传时间不代表调查时间 |
| 真实性与许可 | 页面没有调查机构、采样方法、采集时间、地理范围或生成方法；许可标注为 CC0: Public Domain | 真实调查或合成数据均无法确认；按发布页 CC0 标注允许复制、修改和再分发，项目保留来源与不确定性说明 |

## 总消费的计算口径

总消费为以下十项之和：Rent、Groceries、Eating Out、Entertainment、Subscription Services、Education、Online Shopping、Travel、Fitness、Miscellaneous，均使用原始 USD 数值。Savings 与 Investments 不计入消费，ID、Age 和 Income 也不计入。

若把储蓄和投资也计入，得到的是另一项“全部资金分配”指标：r = -0.002202534338273623，超过收入的比例为 1,583 / 1,700 = 93.11764705882354%。这不能替代消费口径。两个核心结果的匹配取决于正确区分消费与金融资产分配，而不是更换样本或剔除记录。

数据源没有说明金额是月度还是年度。复现只能沿用报告的数值比较，并明确假定收入与支出可比较；不能据此认定记录者负债或处于财务困境。

## 完整字段及实际范围

| 字段 | 最小值 | 最大值 |
| --- | ---: | ---: |
| ID | 1 | 1700 |
| Age | 18 | 27 |
| Income (USD) | 1501 | 7994 |
| Rent (USD) | 300 | 1999 |
| Groceries (USD) | 100 | 599 |
| Eating Out (USD) | 50 | 499 |
| Entertainment (USD) | 20 | 399 |
| Subscription Services (USD) | 10 | 99 |
| Education (USD) | 0 | 1996 |
| Online Shopping (USD) | 20 | 699 |
| Savings (USD) | 100 | 2999 |
| Investments (USD) | 0 | 4999 |
| Travel (USD) | 53 | 1998 |
| Fitness (USD) | 10 | 299 |
| Miscellaneous (USD) | 20 | 399 |

## 可追溯证据

- [官方数据页面](https://www.kaggle.com/datasets/manandkumar/gen-z-money-spending-dataset)
- [官方版本与许可元数据 API](https://www.kaggle.com/api/v1/datasets/view/manandkumar/gen-z-money-spending-dataset)
- [固定版本 1 下载地址](https://www.kaggle.com/api/v1/datasets/download/manandkumar/gen-z-money-spending-dataset?datasetVersionNumber=1)
- [Creative Commons 对 CC0 的官方说明](https://creativecommons.org/publicdomain/zero/1.0/)
- CSV SHA-256：`7f11ed0fd2e95de43687d84ad6ee7d575b0c61f7a06d4522bffe15fb6c8dab41`

恢复后的项目会将财务和购物数据分开，保留来源真实性未知与金额周期未说明的限制。匹配这两个指标不等于原报告所有解释均已得到验证。
