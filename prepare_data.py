#!/usr/bin/env python3
"""
Prepare the committed dataset for the dashboard.

Source: the Global Superstore workbook (`GlobalSuperstore Data.xls`), the classic
Tableau sample that is also distributed on Kaggle as "Global Superstore Data"
(https://www.kaggle.com/datasets/rohitgrewal/global-superstore-data).
It ships as three sheets: Orders, Returns, People.

This script joins the Returns flag onto Orders and writes ONE CSV, which is what
the repository commits (the workbook itself is 18 MB and is not committed).
"""
from pathlib import Path

import pandas as pd

SRC = Path("/tmp/ge/downloads/GlobalSuperstore Data.xls")
OUT = Path(__file__).parent / "data" / "superstore.csv"

orders = pd.read_excel(SRC, sheet_name="Orders")
returns = pd.read_excel(SRC, sheet_name="Returns")
people = pd.read_excel(SRC, sheet_name="People")

print(f"Orders  {orders.shape}\nReturns {returns.shape}\nPeople  {people.shape}\n")

# --- join the return flag -------------------------------------------------
returned_ids = set(returns["Order ID"])
orders["Returned"] = orders["Order ID"].isin(returned_ids)
n_orders = orders["Order ID"].nunique()
print(f"Returns 表覆盖 {returns['Order ID'].nunique():,} 个订单；"
      f"Orders 共 {n_orders:,} 个订单 → 订单级退货率 {returns['Order ID'].nunique() / n_orders * 100:.2f}%")
print(f"合并后匹配上的订单行: {orders['Returned'].sum():,} / {len(orders):,} = "
      f"{orders['Returned'].mean() * 100:.2f}%\n")

# --- types ----------------------------------------------------------------
orders["Order Date"] = pd.to_datetime(orders["Order Date"])
orders["Ship Date"] = pd.to_datetime(orders["Ship Date"])
orders["Order Year"] = orders["Order Date"].dt.year
orders["Order Month"] = orders["Order Date"].dt.to_period("M").astype(str)
orders["Lead Days"] = (orders["Ship Date"] - orders["Order Date"]).dt.days

# --- write ----------------------------------------------------------------
orders.to_csv(OUT, index=False, encoding="utf-8")
print(f"✓ 已写出 {OUT}  ({OUT.stat().st_size / 1024 / 1024:.1f} MB, {len(orders):,} 行 × {orders.shape[1]} 列)\n")

# --- 关键业务数字 ---------------------------------------------------------
print("=" * 76)
print("期间与总量")
print(f"  订单日期 {orders['Order Date'].min().date()} ~ {orders['Order Date'].max().date()}")
print(f"  订单 {n_orders:,}   订单行 {len(orders):,}   客户 {orders['Customer ID'].nunique():,}")
print(f"  销售额 {orders.Sales.sum():,.0f}   利润 {orders.Profit.sum():,.0f}   "
      f"利润率 {orders.Profit.sum() / orders.Sales.sum() * 100:.1f}%")
print(f"  亏损订单行 {(orders.Profit < 0).mean() * 100:.1f}%   亏损金额 {orders.loc[orders.Profit < 0, 'Profit'].sum():,.0f}")

print("\n" + "=" * 76)
print("折扣档位 vs 利润（仪表盘的核心故事）")
neg = orders.assign(亏=orders.Profit < 0).groupby("Discount")["亏"].mean().mul(100)
g = orders.groupby("Discount").agg(订单行=("Profit", "size"), 销售额=("Sales", "sum"), 利润=("Profit", "sum"))
g["利润率%"] = (g["利润"] / g["销售额"] * 100).round(1)
g["亏损行%"] = neg.round(1)
g["销售额占比%"] = (g["销售额"] / orders.Sales.sum() * 100).round(1)
print(g.round(1).to_string())

bands = pd.cut(orders.Discount, [-0.01, 0.0, 0.1, 0.2, 0.3, 1.0],
               labels=["0%", "1-10%", "11-20%", "21-30%", ">30%"])
bg = orders.groupby(bands, observed=True).agg(订单行=("Profit", "size"), 销售额=("Sales", "sum"), 利润=("Profit", "sum"))
bg["利润率%"] = (bg["利润"] / bg["销售额"] * 100).round(1)
bg["亏损行%"] = orders.assign(亏=orders.Profit < 0).groupby(bands, observed=True)["亏"].mean().mul(100).round(1)
bg["销售额占比%"] = (bg["销售额"] / orders.Sales.sum() * 100).round(1)
print("\n按档位合并:")
print(bg.round(1).to_string())

print("\n" + "=" * 76)
print("各市场")
m = orders.groupby("Market").agg(订单=("Order ID", "nunique"), 订单行=("Profit", "size"),
                                 销售额=("Sales", "sum"), 利润=("Profit", "sum"))
m["利润率%"] = (m["利润"] / m["销售额"] * 100).round(1)
m["平均折扣"] = orders.groupby("Market").Discount.mean().round(3)
m["亏损行%"] = orders.assign(亏=orders.Profit < 0).groupby("Market")["亏"].mean().mul(100).round(1)
m["退货率%"] = orders.groupby("Market").Returned.mean().mul(100).round(2)
print(m.round(1).to_string())

print("\n" + "=" * 76)
print("US 市场各区域（这就是仪表盘的筛选器）")
us = orders[orders.Market == "US"]
r = us.groupby("Region").agg(订单=("Order ID", "nunique"), 订单行=("Profit", "size"),
                             销售额=("Sales", "sum"), 利润=("Profit", "sum"))
r["利润率%"] = (r["利润"] / r["销售额"] * 100).round(1)
r["平均折扣"] = us.groupby("Region").Discount.mean().round(3)
r["亏损行%"] = us.assign(亏=us.Profit < 0).groupby("Region")["亏"].mean().mul(100).round(1)
r["深折扣行%"] = us.assign(深=us.Discount >= 0.3).groupby("Region")["深"].mean().mul(100).round(1)
print(r.round(1).to_string())

print("\n" + "=" * 76)
print("品类 / 子品类")
c = orders.groupby("Category").agg(订单行=("Profit", "size"), 销售额=("Sales", "sum"), 利润=("Profit", "sum"))
c["利润率%"] = (c["利润"] / c["销售额"] * 100).round(1)
c["平均折扣"] = orders.groupby("Category").Discount.mean().round(3)
print(c.round(1).to_string())
sc = orders.groupby("Sub-Category").agg(销售额=("Sales", "sum"), 利润=("Profit", "sum"),
                                        平均折扣=("Discount", "mean"), 行数=("Profit", "size"))
sc["利润率%"] = (sc["利润"] / sc["销售额"] * 100).round(1)
print("\n亏损最重的 8 个子品类:")
print(sc.sort_values("利润").head(8).round(2).to_string())
print("\n最赚钱的 8 个子品类:")
print(sc.sort_values("利润", ascending=False).head(8).round(2).to_string())

print("\n" + "=" * 76)
print("各年（趋势图用）")
y = orders.groupby("Order Year").agg(订单行=("Profit", "size"), 销售额=("Sales", "sum"), 利润=("Profit", "sum"))
y["利润率%"] = (y["利润"] / y["销售额"] * 100).round(2)
y["平均折扣"] = orders.groupby("Order Year").Discount.mean().round(4)
y["亏损行%"] = orders.assign(亏=orders.Profit < 0).groupby("Order Year")["亏"].mean().mul(100).round(1)
print(y.round(2).to_string())

mo = orders.groupby("Order Month").agg(销售额=("Sales", "sum"), 利润=("Profit", "sum"))
mo["利润率%"] = (mo["利润"] / mo["销售额"] * 100).round(1)
print(f"\n月度序列 {len(mo)} 个月，首 {mo.index[0]}，末 {mo.index[-1]}")

print("\n" + "=" * 76)
print("退货")
print(f"  整体订单退货率 {orders.groupby('Order ID').Returned.first().mean() * 100:.2f}%")
rr = orders.groupby("Category").Returned.mean().mul(100).round(2)
print("  各品类订单行退货率:", rr.to_dict())
print("  订单优先级:", orders["Order Priority"].value_counts().to_dict())
print("  发货方式:", orders["Ship Mode"].value_counts().to_dict())
print("  细分市场:", orders["Segment"].value_counts().to_dict())
print("  缺失值:\n", orders.isna().sum()[orders.isna().sum() > 0].to_string())
