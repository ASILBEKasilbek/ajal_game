
import turtle
import math

# Ekranni sozlash
ekran = turtle.Screen()
ekran.title("Trigonometrik Funksiyalar Grafigi")
ekran.bgcolor("white")
ekran.setup(width=1000, height=700)

# Turtle obyektini yaratish
qalam = turtle.Turtle()
qalam.speed(0)  # Eng tez chizish

def koordinata_sistemasi():
    """X va Y o'qlarini chizish"""
    qalam.pensize(2)
    qalam.color("black")
    
    # X o'qi
    qalam.penup()
    qalam.goto(-450, 0)
    qalam.pendown()
    qalam.goto(450, 0)
    
    # Y o'qi
    qalam.penup()
    qalam.goto(0, -300)
    qalam.pendown()
    qalam.goto(0, 300)
    
    # O'q belgilari
    qalam.penup()
    qalam.goto(450, -20)
    qalam.write("X", font=("Arial", 14, "bold"))
    qalam.goto(10, 280)
    qalam.write("Y", font=("Arial", 14, "bold"))

def belgila_qoyish():
    """O'qlarga belgilar qo'yish"""
    qalam.pensize(1)
    
    # X o'qidagi belgilar (π belgilari)
    for i in range(-2, 3):
        if i != 0:
            x = i * 100
            qalam.penup()
            qalam.goto(x, -5)
            qalam.pendown()
            qalam.goto(x, 5)
            qalam.penup()
            qalam.goto(x, -25)
            if i == -2:
                qalam.write("-2π", align="center", font=("Arial", 10))
            elif i == -1:
                qalam.write("-π", align="center", font=("Arial", 10))
            elif i == 1:
                qalam.write("π", align="center", font=("Arial", 10))
            elif i == 2:
                qalam.write("2π", align="center", font=("Arial", 10))
    
    # Y o'qidagi belgilar
    for i in [-2, -1, 1, 2]:
        y = i * 50
        qalam.penup()
        qalam.goto(-5, y)
        qalam.pendown()
        qalam.goto(5, y)
        qalam.penup()
        qalam.goto(-25, y - 5)
        qalam.write(str(i), align="right", font=("Arial", 10))

def sinus_chizish():
    """Sin(x) funksiyasini chizish"""
    qalam.pensize(2)
    qalam.color("red")
    
    x = -2 * math.pi
    # Boshlang'ich nuqta
    qalam.penup()
    qalam.goto(x * 100 / math.pi, math.sin(x) * 50)
    qalam.pendown()
    
    # Grafikni chizish
    while x <= 2 * math.pi:
        y = math.sin(x)
        ekran_x = x * 100 / math.pi
        ekran_y = y * 50
        qalam.goto(ekran_x, ekran_y)
        x += 0.01

def cosinus_chizish():
    """Cos(x) funksiyasini chizish"""
    qalam.pensize(2)
    qalam.color("blue")
    
    x = -2 * math.pi
    # Boshlang'ich nuqta
    qalam.penup()
    qalam.goto(x * 100 / math.pi, math.cos(x) * 50)
    qalam.pendown()
    
    # Grafikni chizish
    while x <= 2 * math.pi:
        y = math.cos(x)
        ekran_x = x * 100 / math.pi
        ekran_y = y * 50
        qalam.goto(ekran_x, ekran_y)
        x += 0.01

def tangens_chizish():
    """Tan(x) funksiyasini chizish (cheklangan oraliqda)"""
    qalam.pensize(2)
    qalam.color("green")
    
    # Tangens funksiyasi ±π/2 nuqtalarda aniqlanmagan
    oraliqlar = [
        (-2 * math.pi, -3 * math.pi / 2 - 0.1),
        (-3 * math.pi / 2 + 0.1, -math.pi / 2 - 0.1),
        (-math.pi / 2 + 0.1, math.pi / 2 - 0.1),
        (math.pi / 2 + 0.1, 3 * math.pi / 2 - 0.1),
        (3 * math.pi / 2 + 0.1, 2 * math.pi)
    ]
    
    for bosh, oxir in oraliqlar:
        x = bosh
        qalam.penup()
        y = math.tan(x)
        # Y qiymatini cheklash
        if -6 < y < 6:
            qalam.goto(x * 100 / math.pi, y * 50)
            qalam.pendown()
        
        while x <= oxir:
            y = math.tan(x)
            ekran_x = x * 100 / math.pi
            # Tangens qiymatini ekran chegarasida cheklash
            if -6 < y < 6:
                ekran_y = y * 50
                if not qalam.isdown():
                    qalam.penup()
                    qalam.goto(ekran_x, ekran_y)
                    qalam.pendown()
                else:
                    qalam.goto(ekran_x, ekran_y)
            else:
                qalam.penup()
            x += 0.01

def legenda():
    """Legenda qo'shish"""
    qalam.penup()
    qalam.goto(-430, 250)
    
    # Sin(x)
    qalam.color("red")
    qalam.goto(-430, 250)
    qalam.pendown()
    qalam.goto(-400, 250)
    qalam.penup()
    qalam.goto(-395, 245)
    qalam.color("black")
    qalam.write("y = sin(x)", font=("Arial", 12))
    
    # Cos(x)
    qalam.color("blue")
    qalam.goto(-430, 220)
    qalam.pendown()
    qalam.goto(-400, 220)
    qalam.penup()
    qalam.goto(-395, 215)
    qalam.color("black")
    qalam.write("y = cos(x)", font=("Arial", 12))
    
    # Tan(x)
    qalam.color("green")
    qalam.goto(-430, 190)
    qalam.pendown()
    qalam.goto(-400, 190)
    qalam.penup()
    qalam.goto(-395, 185)
    qalam.color("black")
    qalam.write("y = tan(x)", font=("Arial", 12))

# Grafikni chizish
koordinata_sistemasi()
belgila_qoyish()
sinus_chizish()
cosinus_chizish()
tangens_chizish()
legenda()

# Turtle ni yashirish
qalam.hideturtle()

# Oynani ochiq ushlab turish
ekran.mainloop()