from django.http import JsonResponse,HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from .models import User, CreditScore, LoanApplication, EMIDetail, Payment
from .tasks import calculate_credit_score
from datetime import date,timedelta
from decimal import Decimal,ROUND_HALF_UP

from .tasks import test_func
from .utils import calculate_emi,recalculate_emi

# Create your views here.

def test(request):
    test_func.delay()
    return HttpResponse("Done")

LOAN_AMOUNT_BOUNDS = {
    'Car': 750000,
    'Home': 8500000,
    'Education': 5000000,
    'Personal': 1000000,
}


@api_view(['POST'])
def register_user(request):
    try:
        aadhar_id = request.data.get('aadhar_id')
        name = request.data.get('name')
        email_id = request.data.get('email_id')
        annual_income = request.data.get('annual_income')

        user = User.objects.create(
            unique_user_id=aadhar_id,
            name=name,
            email_id=email_id,
            annual_income=annual_income
        )

        calculate_credit_score.delay(user.unique_user_id)

        return JsonResponse({'unique_user_id': user.unique_user_id}, status=status.HTTP_200_OK)
    except Exception as e:
        return JsonResponse({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)






@api_view(['POST'])
def apply_loan(request):
    data = request.data
    try:
        user = User.objects.get(unique_user_id=data['unique_user_id'])
        credit_score_obj = CreditScore.objects.get(user=user)
        
        if credit_score_obj.score < 400:
            return Response({'Error': 'Credit score too low.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.annual_income < 150000:
            return Response({'Error': 'Annual income too low.'}, status=status.HTTP_400_BAD_REQUEST)
        
        loan_type = data['loan_type']
        loan_amount = float(data['loan_amount'])
        if loan_amount > LOAN_AMOUNT_BOUNDS.get(loan_type, 0):
            return Response({'Error': 'Loan amount exceeds limit for the selected loan type.'}, status=status.HTTP_400_BAD_REQUEST)
        
        interest_rate = float(data['interest_rate'])
        term_period = int(data['term_period'])
        monthly_income = user.annual_income / 12
        monthly_interest_amount = (loan_amount * (interest_rate / 100)) / 12
        print("Calculating emi now")
        emi_amount, error_message = calculate_emi(loan_amount, interest_rate, term_period, monthly_income)
        print(emi_amount)
        if emi_amount is None:
            return Response({'Error': error_message}, status=status.HTTP_400_BAD_REQUEST)
        
        disbursement_date = date.fromisoformat(data['disbursement_date'])
        first_due_date = disbursement_date + timedelta(days=30)
        first_due_date = first_due_date.replace(day=1)

        emi_amount, error_message = calculate_emi(loan_amount, interest_rate, term_period, monthly_income)
        if emi_amount is None:
            return Response({'Error': error_message}, status=status.HTTP_400_BAD_REQUEST)
        
        emi_amount = Decimal(emi_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_payment_expected = emi_amount * term_period
        total_payment_planned = emi_amount * (term_period - 1)
        last_emi_amount = total_payment_expected - total_payment_planned
        last_emi_amount = last_emi_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        loan_application = LoanApplication.objects.create(
            user=user,
            loan_type=loan_type,
            loan_amount=Decimal(loan_amount),
            interest_rate=Decimal(interest_rate),
            term_period=term_period,
            disbursement_date=disbursement_date
        )
        
        due_dates = []
        for month in range(1, term_period + 1):
            due_date = first_due_date + timedelta(days=30 * month)
            amount_due = emi_amount if month < term_period else last_emi_amount
            amount_due = amount_due.quantize(Decimal('0.01'))

            EMIDetail.objects.create(
                loan_application=loan_application,
                date=due_date,
                amount_due=amount_due,
                interest_for_month=monthly_interest_amount
            )
            due_dates.append({
                'Date': due_date.isoformat(),
                'Amount_due': amount_due
            })

        return Response({
            'Loan_id': loan_application.loan_id.hex,
            'Due_Dates': due_dates,
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'Error': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)
    except CreditScore.DoesNotExist:
        return Response({'Error': 'Credit score not found for user.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['POST'])
def make_payment(request):
    loan_id = request.data.get('loan_id')
    amount = Decimal(request.data.get('amount'))
    date_of_payment = date.fromisoformat(request.data.get('date'))

    try:
        loan_application = LoanApplication.objects.get(loan_id=loan_id)
        emis = EMIDetail.objects.filter(loan_application=loan_application).order_by('date')

        for emi in emis:
            if emi.date < date_of_payment:
                amount_paid_for_emi = Payment.objects.filter(emi_detail=emi).aggregate(Sum('amount_paid'))['amount_paid__sum'] or Decimal('0.0')
                if amount_paid_for_emi < emi.amount_due:
                    return Response({'Error': 'Previous EMIs are due'}, status=400)
            else:
                break

        emi_for_payment = emis.filter(date__gte=date_of_payment).first()
        if not emi_for_payment:
            return Response({'Error': 'No EMIs available for payment on or after the specified date'}, status=400)


        if Payment.objects.filter(emi_detail=emi_for_payment,payment_date=date_of_payment).exists():
            return Response({'Error': 'Payment is already made for that date'}, status=400)
        
        total_paid_for_emi = Payment.objects.filter(emi_detail=emi_for_payment).aggregate(Sum('amount_paid'))['amount_paid__sum'] or Decimal('0.0')
        # If the payment is not exactly the amount due, recalculate EMI
        if total_paid_for_emi + amount != emi_for_payment.amount_due:
            print("Recalculating emi since payment made was different")
            recalculate_emi(loan_application, date_of_payment)

        print("Creating payment object")
        Payment.objects.create(emi_detail=emi_for_payment, amount_paid=amount, payment_date=date_of_payment)

        return Response({'loan_id': loan_application.loan_id.hex}, status=200)
    except LoanApplication.DoesNotExist:
        return Response({'Error': 'Loan not found'}, status=400)
    except Exception as e:
        return Response({'Error': str(e)}, status=400) 
    



@api_view(['GET'])
def get_statement(request):
    loan_id = request.query_params.get('loan_id')
    loan_application = get_object_or_404(LoanApplication, loan_id=loan_id)

    input_date = date.fromisoformat(request.query_params.get('date'))

    past_emis = EMIDetail.objects.filter(loan_application=loan_application, date__lt=input_date).order_by('date')
    past_transactions = []
    for emi in past_emis:
        payments = Payment.objects.filter(emi_detail=emi)
        for payment in payments:
            past_transactions.append({
                'Date': payment.payment_date,
                'Principal': emi.amount_due - emi.interest_for_month,  
                'Interest': emi.interest_for_month,
                'Amount_paid': payment.amount_paid,
            })


    upcoming_emis = EMIDetail.objects.filter(loan_application=loan_application, date__gte=input_date).order_by('date')
    upcoming_transactions = [{
        'Date': emi.date,
        'Amount_due': emi.amount_due,
    } for emi in upcoming_emis]

    return Response({
        'Past_transactions': past_transactions,
        'Upcoming_transactions': upcoming_transactions
    })    