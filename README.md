# TaxiBot

## 🇺🇿 O'zbekcha Tavsif

### 🟩 Umumiy Ma'lumot

**TaxiBot** — ikki yo‘nalish bo‘yicha taxi buyurtmalarini avtomatlashtiruvchi bot bo‘lib, haydovchi va mijoz o‘rtasidagi jarayonlarni soddalashtiradi. Bot buyurtmalarni haydovchilar guruhiga yuboradi, guruhni tartibga soladi, haydovchilarning obuna muddati va to‘lov holatini avtomatik boshqaradi.

---

## 🚖 Asosiy Imkoniyatlar

### **1. Mijozlar Uchun Jarayon**

* Yo‘nalishni tanlaydi.
* Haydovchi uchun izoh qoldirishi mumkin.
* Buyurtma darhol haydovchilar guruhiga yuboriladi.
* Buyurtmada haydovchi uchun "Mijozga yozish" inline tugmalar mavjud.

---

### **2. Public Guruh Nazorati**

TaxiBot public guruhga ulangan bo‘ladi va moderator sifatida ishlaydi:

* Ro‘yxatdan o‘tmagan haydovchilar reklamalarini aniqlaydi.
* Xabarni avtomatik o‘chiradi.
* "E'lon joylashtirish uchun ro‘yxatdan o‘ting" deb ogohlantiradi.
* Guruhda yozishni cheklaydi.
* Taxi bilan bog‘liq bo‘lmagan xabarlarni o‘chiradi.
* Oddiy foydalanuvchi taxi so‘rasa, xabar o‘chiriladi va haydovchilar guruhiga forward qilinadi.

---

### **3. Haydovchilar Ro‘yxatdan O‘tishi va To‘lov Tasdiqlash**

* Haydovchi botga chek yuboradi.
* Adminlar chekni **Tasdiqlash** / **Rad etish** tugmalari bilan oladi.
* Bir admin qaror qabul qilgach, boshqalar bosolmaydi.
* Agar ular bossa: *"Bu chek allaqachon tasdiqlangan yoki rad etilgan"* degan alert chiqadi.
* Tasdiqlangach haydovchi `drivers` bazasiga qo‘shiladi.
* Guruhdagi cheklovlar avtomatik olib tashlanadi.
* Har bir haydovchiga individual **group_id** biriktiriladi.

---

### **4. Obuna Muddatini Boshqarish**

* Bot haydovchi obuna muddatini tekshirib boradi.
* Muddati tugasa — avtomatik haydovchilar guruhidan chiqaradi.
* Tugashiga 2 kun qolganda haydovchiga ogohlantirish yuboradi.

---

### 🌐 Til Qo‘llab-quvvatlashi

* **O‘zbek tili**

---

## 🇬🇧 English Version

## 🟩 Overview

**TaxiBot** is a dual-direction taxi service automation bot designed to connect passengers and drivers efficiently while maintaining strict moderation and payment validation workflows.

Bot streamlines the ordering process, manages driver subscription periods, and enforces group rules to keep public taxi groups clean and professional.

---

## 🚖 Key Features

### **1. Passenger Workflow**

* Users select the trip direction.
* They can optionally leave a comment for the driver.
* Orders are sent directly to the drivers’ private group.
* Each order includes inline action buttons("Write to client") for quick interactions.

---

### **2. Public Group Protection**

TaxiBot is connected to a public taxi group and acts as a moderator:

* Detects unregistered drivers posting advertisements.
* Instantly deletes such messages.
* Notifies the user about the need to register before posting.
* Automatically restricts them from sending further messages.
* Removes any irrelevant or non-taxi-related messages.
* If a regular user asks for a taxi, the bot deletes the message and forwards it to the drivers’ group.

---

### **3. Driver Registration & Payment Validation**

* Drivers send payment receipts to the bot.
* All admins receive the receipt with **Accept** / **Reject** buttons.
* Once one admin makes a decision, others can no longer interact.
* If another admin clicks afterward, an alert appears:
  *"This receipt has already been approved or rejected."*
* Approved drivers are added to the `drivers` database table.
* Posting restrictions in the group are automatically removed.
* Drivers are assigned a specific group ID.

---

### **4. Subscription Management**

* The bot tracks each driver's subscription period.
* When their paid period expires, the bot automatically removes them from the drivers' group via their assigned group ID.
* Drivers receive a notification **2 days before** the subscription expires.

---

## 🌐 Languages

TaxiBot supports:

* **O'zbek (Uzbek)**

---
