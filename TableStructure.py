from prettytable import PrettyTable

table = PrettyTable([
    "","挂牌编号","房产证编号","房源核验统一编码","所属小区","所属城区","建筑面积",
])
table.padding_width = 2
table.add_row([
    "字段名称","gpID","fczID","fyID","block","district","area",
])
table.add_row([
    "字段类型","varchar(100)","varchar(100)","varchar(100)","varchar(100)","varchar(100)","float",
])
print(table)
table = PrettyTable([
    "","委托价格","挂牌时间","挂牌机构名称","挂牌人员","是否有图","创建时间",
])
table.padding_width = 2
table.add_row([
    "字段名称","price","gp_date","org_name","person","has_pic","created",])
table.add_row([
    "字段类型","float","date","varchar(100)","varchar(100)","varchar(100)","timestrap",])
print(table)
