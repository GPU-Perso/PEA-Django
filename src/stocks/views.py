from typing import List, Tuple, Any

from django.shortcuts import render

from stocks import stock
from stocks.stock import load_stocks, Stock, list_alerts


# Create your views here.
def stocks_list(request, online=False):
    data = load_stocks(bool(online))
    return render(request, "stocks/index.html", context={
        'stocks_list': data, "online": online, 'stock_interval_min': stock.UPDATE_STOCK_DELAY_MIN,
        'stock_interval_max': stock.UPDATE_STOCK_DELAY_MAX,'etf_interval_min': stock.UPDATE_ETF_DELAY_MIN,
        'etf_interval_max': stock.UPDATE_ETF_DELAY_MAX
    })


def stock_update(request, code):
    s = Stock(code)
    s.update()
    return render(request, "stocks/row.html", context={'stock': s})

def show_alerts(request):
    alerts = list_alerts()
    return render(request, "stocks/alerts.html", context={'alerts': alerts})

def acknowledge_alert(request, id):
    stock.acknowledge_alert(id)
    return show_alerts(request)

def show_stock(request):
    params = request.GET
    if "code" in params:
        s = Stock(params["code"])
        s.load()
        if "buy_price" in params:
            try:
                s.buy_price = float(params["buy_price"])
            except (ValueError):
                s.buy_price = 0
            try:
                s.sell_price = float(params["sell_price"])
            except (ValueError):
                s.sell_price = 0
            try:
                s.nb = int(params["nb"])
            except (ValueError):
                s.nb = 0
            s.name = params["name"]
            if "active" in params and params["active"] == "on":
                s.active = True
            else:
                s.active = False
            if "is_etf" in params and params["is_etf"] == "on":
                s.is_etf = True
            else:
                s.is_etf = False
            s.link = params["link"]

        s.store()
    else:
        code = ""
        s = Stock(code)

    return render(request, "stocks/detail.html", context={'stock': s})
