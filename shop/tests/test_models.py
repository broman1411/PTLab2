from django.test import TestCase
from shop.models import Product, Purchase, Customer
from datetime import datetime

class CustomerTestCase(TestCase):
    def setUp(self):
        self.customer1 = Customer.objects.create(name="Иван Иванов", total_purchases=3)
        self.customer2 = Customer.objects.create(name="Петр Петров", total_purchases=8)
        self.customer3 = Customer.objects.create(name="Сидор Сидоров", total_purchases=12)
        self.customer4 = Customer.objects.create(name="Анна Аннова", total_purchases=18)
        self.customer5 = Customer.objects.create(name="Мария Максимова", total_purchases=25)
    
    def test_discount_levels(self):
        """Тестируем расчет уровней скидок"""
        self.assertEqual(self.customer1.discount_level, 0)   # 3 покупки - нет скидки
        self.assertEqual(self.customer2.discount_level, 5)   # 8 покупок - 5%
        self.assertEqual(self.customer3.discount_level, 10)  # 12 покупок - 10%
        self.assertEqual(self.customer4.discount_level, 15)  # 18 покупок - 15%
        self.assertEqual(self.customer5.discount_level, 20)  # 25 покупок - 20%
    
    def test_discount_percent(self):
        """Тестируем получение процента скидки"""
        self.assertEqual(self.customer1.discount_percent, 0)
        self.assertEqual(self.customer2.discount_percent, 5)
        self.assertEqual(self.customer3.discount_percent, 10)
    
    def test_customer_creation(self):
        """Тестируем создание покупателя"""
        self.assertEqual(self.customer1.name, "Иван Иванов")
        self.assertEqual(self.customer1.total_purchases, 3)
        self.assertEqual(self.customer1.total_spent, 0)
    
    def test_customer_string_representation(self):
        """Тестируем строковое представление покупателя"""
        self.assertIn("Иван Иванов", str(self.customer1))
        self.assertIn("Покупок: 3", str(self.customer1))
        self.assertIn("Скидка: 0%", str(self.customer1))


class PurchaseWithCustomerTestCase(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Тестовый Покупатель", total_purchases=4)
        self.product = Product.objects.create(name="Телевизор", price=10000)
    
    def test_purchase_without_discount(self):
        """Тестируем покупку без скидки (менее 5 покупок)"""
        # У покупателя 4 покупки, скидка 0%
        purchase = Purchase.objects.create(
            product=self.product,
            person="Тестовый Покупатель",
            address="Тестовая ул.",
            customer=self.customer
        )
        
        # Проверяем что цена без скидки
        self.assertEqual(purchase.final_price, 10000)
        
        # Проверяем обновление статистики покупателя
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.total_purchases, 5)
        self.assertEqual(self.customer.total_spent, 10000)
    
    def test_purchase_with_discount_after_threshold(self):
        """Тестируем покупку со скидкой после достижения порога"""
        # Сначала создаем покупку чтобы достичь 5 покупок
        purchase1 = Purchase.objects.create(
            product=self.product,
            person="Тестовый Покупатель",
            address="Тестовая ул.",
            customer=self.customer
        )
        
        # Вторая покупка - уже должна быть со скидкой 5%
        purchase2 = Purchase.objects.create(
            product=self.product,
            person="Тестовый Покупатель",
            address="Тестовая ул.",
            customer=self.customer
        )
        
        expected_price = 10000 * 95 // 100  # 5% скидка = 9500
        self.assertEqual(purchase2.final_price, expected_price)
        
        # Проверяем обновление статистики
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.total_purchases, 6)
        self.assertEqual(self.customer.total_spent, 10000 + expected_price)
    
    def test_purchase_without_customer(self):
        """Тестируем покупку без регистрации покупателя"""
        purchase = Purchase.objects.create(
            product=self.product,
            person="Гость",
            address="Гостевая ул."
        )
        
        self.assertEqual(purchase.final_price, self.product.price)
        self.assertIsNone(purchase.customer)
    
    def test_multiple_discount_levels(self):
        """Тестируем несколько уровней скидок"""
        customer = Customer.objects.create(name="ВИП Покупатель", total_purchases=9)
        product = Product.objects.create(name="Холодильник", price=20000)
        
        # 10-я покупка - скидка 5%
        purchase1 = Purchase.objects.create(
            product=product,
            person="ВИП Покупатель",
            address="ВИП ул.",
            customer=customer
        )
        expected_price1 = 20000 * 95 // 100  # 5% скидка
        self.assertEqual(purchase1.final_price, expected_price1)
        
        # 14-я покупка - скидка 10%
        customer.total_purchases = 13
        customer.save()
        purchase2 = Purchase.objects.create(
            product=product,
            person="ВИП Покупатель", 
            address="ВИП ул.",
            customer=customer
        )
        expected_price2 = 20000 * 90 // 100  # 10% скидка
        self.assertEqual(purchase2.final_price, expected_price2)


class ProductTestCase(TestCase):
    def setUp(self):
        Product.objects.create(name="book", price="740")
        Product.objects.create(name="pencil", price="50")

    def test_correctness_types(self):                   
        self.assertIsInstance(Product.objects.get(name="book").name, str)
        self.assertIsInstance(Product.objects.get(name="book").price, int)
        self.assertIsInstance(Product.objects.get(name="pencil").name, str)
        self.assertIsInstance(Product.objects.get(name="pencil").price, int)        

    def test_correctness_data(self):
        self.assertTrue(Product.objects.get(name="book").price == 740)
        self.assertTrue(Product.objects.get(name="pencil").price == 50)
    
    def test_product_string_representation(self):
        """Тестируем строковое представление товара"""
        product = Product.objects.get(name="book")
        self.assertEqual(str(product), "book")


class PurchaseTestCase(TestCase):
    def setUp(self):
        self.product_book = Product.objects.create(name="book", price="740")
        self.datetime = datetime.now()
        Purchase.objects.create(product=self.product_book,
                                person="Ivanov",
                                address="Svetlaya St.")

    def test_correctness_types(self):
        self.assertIsInstance(Purchase.objects.get(product=self.product_book).person, str)
        self.assertIsInstance(Purchase.objects.get(product=self.product_book).address, str)
        self.assertIsInstance(Purchase.objects.get(product=self.product_book).date, datetime)

    def test_correctness_data(self):
        self.assertTrue(Purchase.objects.get(product=self.product_book).person == "Ivanov")
        self.assertTrue(Purchase.objects.get(product=self.product_book).address == "Svetlaya St.")
        self.assertTrue(Purchase.objects.get(product=self.product_book).date.replace(microsecond=0) == \
            self.datetime.replace(microsecond=0))
    
    def test_purchase_string_representation(self):
        """Тестируем строковое представление покупки"""
        purchase = Purchase.objects.get(product=self.product_book)
        self.assertIn("Покупка: book", str(purchase))
        self.assertIn("Ivanov", str(purchase))