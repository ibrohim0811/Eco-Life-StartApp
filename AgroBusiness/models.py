import uuid
from django.db import models
from django.utils.text import slugify
from datetime import datetime, timedelta, timezone
from django.core.validators import MaxValueValidator, MinValueValidator




class BaseCreatedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True



class Product(BaseCreatedModel):
    
    name = models.CharField(max_length=500)
    slug = models.SlugField(editable=False)
    price = models.IntegerField()
    sale = models.IntegerField(default=0, validators=[MaxValueValidator(100), MinValueValidator(0)])
    is_active = models.BooleanField()
    about = models.TextField()
    count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    info = models.JSONField(default=dict, blank=True, null=True)
    

    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
        while Product.objects.filter(slug = self.slug).exclude(pk=self.pk).exists():
            slugger = str(uuid.uuid4()).split('-')[-1]
            self.slug = f"{base_slug}-{slugger}"
        return super().save(*args, **kwargs)
    
    
    @property
    def is_new(self):
        now = datetime.now(timezone.utc)
        farq = now - self.created_at
        
        if farq > timedelta(days=2):
            return False
        else:
            return True
    
    
    @property
    def sale_seller(self):
        return int(self.price - (self.price * self.sale / 100))
    
    
    class Meta:
        ordering = ['-created_at'] 
    
    
    def __str__(self):
        return self.name
    
    
    
class ProductImage(BaseCreatedModel):
    image = models.ImageField(upload_to='products/')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    
    def __str__(self):
        return self.product.name
