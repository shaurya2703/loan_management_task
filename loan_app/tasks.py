from celery import shared_task
from .models import User, CreditScore
import pandas as pd

@shared_task(bind=True)
def test_func(self):
    for i in range(10):
        print(i)
    return "Done"    


@shared_task
def calculate_credit_score(user_id):
    user = User.objects.get(pk=user_id)
    
    df = pd.read_csv('/Users/shauryakhanna/Documents/projects/loan_django/loan_management/loan_app/transactions_data.csv')
    user_df = df[df['user'] == user.aadhar_id]
    credit_debit_sum = user_df.groupby('transaction_type')['amount'].sum().to_dict()
    net_balance = credit_debit_sum.get('CREDIT', 0) - credit_debit_sum.get('DEBIT', 0)
    print(f"net balance: {net_balance}")
    if net_balance >= 1000000:
        credit_score = 900
    elif net_balance <= 100000:
        credit_score =  300
    else:
        intervals = net_balance//15000
        credit_score = int(300 + (intervals * 10))
    print(f"Credit Score: {credit_score}")
    CreditScore.objects.create(user=user, score=credit_score)