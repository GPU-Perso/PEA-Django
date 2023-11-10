from django.shortcuts import render

from stocks.stock import load_stocks, Stock


# Create your views here.
def stocks_list(request):
    data = load_stocks(online=False)
    return render(request, "stocks/index.html", context={'stocks_list': data})
def stock_update(request, code):
    s = Stock(code)
    s.load()
    s.store()
    return render(request, "stocks/row.html", context={'stock': s})
