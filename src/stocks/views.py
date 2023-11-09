from django.shortcuts import render

from stocks.stock import load_stocks


# Create your views here.
def stocks_list(request):
    data = load_stocks(online=False)
    return render(request, "stocks/index.html", context={'stocks_list': data})
