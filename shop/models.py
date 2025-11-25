from django.db import models

class Customer(models.Model):
    """Модель покупателя с накопительной системой скидок"""
    name = models.CharField(max_length=200, verbose_name="ФИО покупателя")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    total_purchases = models.PositiveIntegerField(default=0, verbose_name="Общее количество покупок")
    total_spent = models.PositiveIntegerField(default=0, verbose_name="Общая сумма покупок")
    
    # Уровни скидок
    DISCOUNT_LEVELS = [
        (0, '0% - Нет скидки'),
        (5, '5% - Бронзовый уровень'),
        (10, '10% - Серебряный уровень'),
        (15, '15% - Золотой уровень'),
        (20, '20% - Платиновый уровень'),
    ]
    
    @property
    def discount_level(self):
        """Определяет уровень скидки на основе количества покупок"""
        if self.total_purchases >= 20:
            return 20
        elif self.total_purchases >= 15:
            return 15
        elif self.total_purchases >= 10:
            return 10
        elif self.total_purchases >= 5:
            return 5
        else:
            return 0
    
    @property
    def discount_percent(self):
        """Возвращает процент скидки"""
        return self.discount_level
    
    def __str__(self):
        return f"{self.name} (Покупок: {self.total_purchases}, Скидка: {self.discount_percent}%)"

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()
    
    def __str__(self):
        return self.name

class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    person = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Покупатель")
    final_price = models.PositiveIntegerField(null=True, blank=True, verbose_name="Цена со скидкой")
    
    def save(self, *args, **kwargs):
        """Переопределяем save для расчета скидки"""
        # Сначала рассчитываем скидку на основе ТЕКУЩЕГО состояния покупателя
        if self.customer:
            discount = self.customer.discount_percent
            self.final_price = self.product.price * (100 - discount) // 100
        else:
            self.final_price = self.product.price
        
        # Сохраняем покупку
        super().save(*args, **kwargs)
        
        # Затем обновляем статистику покупателя (для СЛЕДУЮЩЕЙ покупки)
        if self.customer:
            self.customer.total_purchases += 1
            self.customer.total_spent += self.final_price
            self.customer.save()
    
    def __str__(self):
        return f"Покупка: {self.product.name} - {self.person}"