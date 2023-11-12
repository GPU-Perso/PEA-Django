from django.shortcuts import render

from stocks.stock import load_stocks, Stock


# Create your views here.
def stocks_list(request, online=False):
    data = load_stocks(bool(online))
    return render(request, "stocks/index.html", context={'stocks_list': data, "online": online})
def stock_update(request, code):
    s = Stock(code)
    s.update()
    return render(request, "stocks/row.html", context={'stock': s})
