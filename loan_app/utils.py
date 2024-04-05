from django.db.models import Sum
from .models import Payment
from decimal import Decimal
from datetime import date

def calculate_emi(principal, annual_interest_rate, tenure_months, monthly_income):
    monthly_interest_rate = annual_interest_rate / 12 / 100
    emi = principal * monthly_interest_rate * ((1 + monthly_interest_rate) ** tenure_months) / (((1 + monthly_interest_rate) ** tenure_months) - 1)
    print(f"EMI : {emi}")
    if emi > (float(monthly_income) * 0.6):
        return None, f"EMI exceeds 60% of monthly income"

    total_interest_payable = (emi * tenure_months) - principal
    print(f"Total interest payable: {total_interest_payable}")
    if total_interest_payable <= 10000:
        return None, "Total interest earned must be greater than 10000"

    return emi, None



def recalculate_emi(loan_application, payment_date):

    total_paid_so_far = Payment.objects.filter(emi_detail__loan_application=loan_application).aggregate(total=Sum('amount_paid'))['total'] or Decimal(0.0)
    remaining_principal = loan_application.loan_amount - total_paid_so_far

    remaining_payments = loan_application.emi_details.exclude(payments__payment_date__lte=payment_date).count()

    if remaining_payments == 0:
        return None, "Loan is fully paid off"

    new_emi, error_message = calculate_emi(remaining_principal, loan_application.interest_rate, remaining_payments, loan_application.user.annual_income / 12)
    if new_emi is not None:
        for emi_detail in loan_application.emi_details.exclude(payments__payment_date__lte=date.today()):
            emi_detail.amount_due = new_emi
            emi_detail.save()

    return new_emi, error_message