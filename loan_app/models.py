from django.db import models
import uuid

class User(models.Model):
    unique_user_id = models.CharField(primary_key=True,max_length=20,editable=False)
    name = models.CharField(max_length=255)
    email_id = models.EmailField(unique=True)
    annual_income = models.DecimalField(max_digits=15, decimal_places=2)


    def __str__(self):
        return f"Name : {self.name}, Email : {self.email_id}, Annual Income: {self.annual_income}"

class CreditScore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return f"{self.user.name}: {self.score}"


class LoanApplication(models.Model):
    LOAN_TYPE_CHOICES = [
        ('Car', 'Car'),
        ('Home', 'Home'),
        ('Education', 'Education'),
        ('Personal', 'Personal'),
    ]

    loan_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=10, choices=LOAN_TYPE_CHOICES)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_period = models.IntegerField()  # in months
    disbursement_date = models.DateField()
    
    def __str__(self):
        return f"{self.loan_type} Loan for {self.user.name}"
    

class EMIDetail(models.Model):
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='emi_details')
    date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    interest_for_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"EMI on {self.date} for {self.loan_application.loan_id}"
    

class Payment(models.Model):
    emi_detail = models.ForeignKey(EMIDetail, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()

    def __str__(self):
        return f"Payment of {self.amount_paid} on {self.payment_date} for {self.emi_detail}"



