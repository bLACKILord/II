# admin.py - административные функции для создания промокодов
from firebase_service import DatabaseService
from config import ADMIN_IDS
import random
import string

db = DatabaseService()


def generate_random_code(length=8):
    """Генерация случайного промокода"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def create_vip_promocode(code=None, uses=1):
    """Создать VIP промокод (навсегда)"""
    if not code:
        code = f"VIP-{generate_random_code(6)}"
    
    db.create_promocode(code, 'vip', uses=uses)
    print(f"✅ VIP промокод создан: {code}")
    print(f"   Использований: {uses}")
    return code


def create_premium_promocode(days, code=None, uses=1):
    """Создать Premium промокод"""
    if not code:
        code = f"PREMIUM-{days}-{generate_random_code(4)}"
    
    db.create_promocode(code, 'premium', days=days, uses=uses)
    print(f"✅ Premium промокод создан: {code}")
    print(f"   Срок: {days} дней")
    print(f"   Использований: {uses}")
    return code


def create_requests_promocode(requests, code=None, uses=1):
    """Создать промокод на дополнительные запросы"""
    if not code:
        code = f"REQ-{requests}-{generate_random_code(4)}"
    
    db.create_promocode(code, 'requests', requests=requests, uses=uses)
    print(f"✅ Промокод на запросы создан: {code}")
    print(f"   Запросов: +{requests}")
    print(f"   Использований: {uses}")
    return code


def admin_menu():
    """Интерактивное меню для админов"""
    print("\n" + "="*50)
    print("🔧 АДМИН ПАНЕЛЬ - СОЗДАНИЕ ПРОМОКОДОВ")
    print("="*50)
    
    while True:
        print("\n1. Создать VIP промокод (навсегда)")
        print("2. Создать Premium промокод (на дни)")
        print("3. Создать промокод на запросы")
        print("4. Массовое создание промокодов")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ").strip()
        
        if choice == "1":
            print("\n--- VIP Промокод ---")
            code = input("Код (Enter для авто): ").strip().upper() or None
            uses = int(input("Использований (1 = одноразовый): ") or 1)
            create_vip_promocode(code, uses)
        
        elif choice == "2":
            print("\n--- Premium Промокод ---")
            days = int(input("Количество дней (7/30/90): "))
            code = input("Код (Enter для авто): ").strip().upper() or None
            uses = int(input("Использований (1 = одноразовый): ") or 1)
            create_premium_promocode(days, code, uses)
        
        elif choice == "3":
            print("\n--- Промокод на запросы ---")
            requests = int(input("Количество запросов: "))
            code = input("Код (Enter для авто): ").strip().upper() or None
            uses = int(input("Использований (1 = одноразовый): ") or 1)
            create_requests_promocode(requests, code, uses)
        
        elif choice == "4":
            print("\n--- Массовое создание ---")
            promo_type = input("Тип (vip/premium/requests): ").lower()
            count = int(input("Количество промокодов: "))
            uses = int(input("Использований каждого: "))
            
            if promo_type == "vip":
                for _ in range(count):
                    create_vip_promocode(uses=uses)
            
            elif promo_type == "premium":
                days = int(input("Количество дней: "))
                for _ in range(count):
                    create_premium_promocode(days, uses=uses)
            
            elif promo_type == "requests":
                requests = int(input("Количество запросов: "))
                for _ in range(count):
                    create_requests_promocode(requests, uses=uses)
        
        elif choice == "0":
            print("\n👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор")


if __name__ == "__main__":
    admin_menu()