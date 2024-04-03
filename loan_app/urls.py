
from django.urls import path
from .views import register_user, apply_loan,make_payment,get_statement,test

urlpatterns = [
    path('',test,name='test'),
    path('api/register-user/', register_user, name='register-user'),
    path('/api/apply-loan/', apply_loan, name='apply-loan'),
    path('/api/make-payment/', make_payment, name='make-payment'),
    path('/api/get-statement/', get_statement, name='get-statement')    
]