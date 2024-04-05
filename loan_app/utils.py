

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



def recalculate_emi(loan_application, payment_amount):

    total_paid_so_far = sum(payment.amount_paid for payment in loan_application.emi_details.payments.all()) + payment_amount
    new_principal = loan_application.loan_amount - total_paid_so_far
    
    original_tenure_months = loan_application.term_period
    payments_made = loan_application.emi_details.payments.count()
    remaining_tenure= original_tenure_months - payments_made
    monthly_income = loan_application.user.annual_income / 12
    
    new_emi, error_message = calculate_emi(new_principal, loan_application.annual_interest_rate, remaining_tenure, monthly_income)

    return new_emi, error_message