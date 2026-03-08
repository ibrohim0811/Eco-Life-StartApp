import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class BaseCreatedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        
    
class Users(AbstractUser):
    
    first_name = models.CharField(max_length=70)
    last_name = models.CharField(max_length=70)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    phone = models.CharField(max_length=20, unique=True)
    about = models.TextField(blank=True, null=True)
    username = models.CharField(max_length=50, unique=True)
    language = models.CharField(max_length=15)
    tg_id = models.BigIntegerField(blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    image = models.ImageField(upload_to='users/', default='users/image.png')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.first_name
    


class BalanceHistory(BaseCreatedModel):
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Tushum'
        EXPENSE = 'EXPENSE', 'Chiqim'

    user = models.ForeignKey(
        Users, 
        on_delete=models.CASCADE, 
        related_name='balance_history'
    )
    
    amount = models.BigIntegerField() 
    
    transaction_type = models.CharField(
        max_length=10, 
        choices=TransactionType.choices
    )
    
    description = models.CharField(max_length=255, blank=True, null=True) 
   
    def __str__(self):
        return f"{self.user.first_name} - {self.amount} ({self.transaction_type})"

    class Meta:
        ordering = ['-created_at'] 
        
            
    
class UserActivities(BaseCreatedModel):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    amount = models.IntegerField(default=2500)
    region = models.CharField(max_length=150)
    video_file_id = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.FloatField()
    latitude = models.FloatField()
    user = models.ForeignKey(
        Users, 
        to_field='phone',  
        on_delete=models.CASCADE, 
        related_name='phone_act',
        db_column='user_phone' 
    )



class Subscription(models.Model):
    FREE = "free"
    GO = "go"
    PRO = "pro"
    ULTIMA = "ultima"

    PLAN_CHOICES = [
        (FREE, "Free"),
        (GO, "Go"),
        (PRO, "Pro"),
        (ULTIMA, "Ultima"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default=FREE)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_lifetime = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self) -> bool:
        if self.plan == self.FREE:
            return True
        if self.is_lifetime:
            return True
        return bool(self.expires_at and self.expires_at > timezone.now())

    def badge_text(self) -> str:
        if self.plan == self.FREE:
            return "FREE"
        return self.plan.upper()
    
    
class Banner(BaseCreatedModel):
    title = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to="banners/")
    link_url = models.CharField(max_length=255, blank=True)  
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0) 

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]
        


class Sale(models.Model):
    ALL = "all"
    SELECTED = "selected"
    RANDOM = "random"
    MODE_CHOICES = [
        (ALL, "All products"),
        (SELECTED, "Selected products"),
        (RANDOM, "Random products"),
    ]

    tag = models.CharField(max_length=30)  
    title = models.CharField(max_length=120, blank=True)

    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default=ALL)

    percent = models.PositiveIntegerField(default=0)  
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    random_count = models.PositiveIntegerField(default=0) 

    is_active = models.BooleanField(default=True)

    products = models.ManyToManyField("AgroBusiness.Product", blank=True, related_name="sale_events")

    def is_live(self):
        now = timezone.now()
        return self.is_active and self.start_at <= now <= self.end_at
    
    

