# Hosty
Web-based software solution for the comprehensive management of small, medium, and boutique hotels.
Here is a professional, academic-level **README.md** written in English, ready to be copied and pasted into your GitHub repository.

I have highlighted the **Data Structures** section, as that is the most important part for your class.


Unlike standard management software, this project focuses on **algorithmic efficiency**. It features **manual implementations of fundamental Data Structures and Algorithms** (from scratch, without relying on built-in Python sort/search libraries) to solve real-world operational problems such as task prioritization, room service queuing, and housekeeping logistics.

-----

## 📸 Dashboard Preview

<img width="2470" height="1288" alt="image" src="https://github.com/user-attachments/assets/59d42292-067b-42a8-84cf-5ec3e87ef6c9" />


> **Key Feature:** The UI is built with **GridStack.js**, allowing a modular, drag-and-drop widget experience.

-----

## 🧠 Data Structures & Algorithms Implemented

This project demonstrates the practical application of Computer Science theory in Software Engineering.

| Feature | Data Structure / Algorithm | Time Complexity | Description |
| :--- | :--- | :--- | :--- |
| **Maintenance** | **Priority Queue** (Bubble Sort) | $O(n^2)$ | Prioritizes tasks based on urgency (Critical \> Low). Uses a manual Bubble Sort algorithm with a FIFO tie-breaker based on timestamp. |
| **Room Service** | **Min-Heap** | $O(1)$ access | Ensures the oldest order is always at the root (top) to be served first. Implements a manual `heapify_up` algorithm. |
| **Waitlist** | **Queue** (FIFO) | $O(1)$ | Strictly First-In, First-Out management for overbooking or restaurant waiting lines. |
| **Housekeeping** | **Linked List** | $O(n)$ | Generates a sequential route (Head $\to$ Next $\to$ Tail) for cleaning staff, allowing dynamic node removal when a room is cleaned. |
| **Guest Lookup** | **Hash Map** | $O(1)$ avg | Direct access to guest data via Room Number using a custom Hash Function (ASCII sum modulo table size). |
| **Guest Search** | **String Search** (Naive) | $O(n \cdot m)$ | Brute-force string matching algorithm to find guest history by name without using SQL `LIKE`. |
| **Do Not Disturb** | **Set** | $O(1)$ | Ensures uniqueness. A room cannot be added twice to the DND list; it either exists in the set or it doesn't. |
| **Key Drop** | **Stack** (LIFO) | $O(1)$ | (Optional) Simulates a key card drop-box where the last key dropped is the first one processed. |

-----

## 🚀 Key Technical Features

  * **Multi-Tenancy Architecture:** The system uses **Data Segregation**. All models (`Rooms`, `Bookings`, `Tasks`) are linked to a specific `User`. This allows multiple hotels to use the platform simultaneously without sharing data.
  * **Real-Time Polling:** The frontend uses asynchronous JavaScript (`fetch`) to poll the API every 5-15 seconds, updating widgets (like the Check-In list or Notifications) without requiring a page reload.
  * **Security:**
      * CSRF Token handling for all AJAX requests.
      * `@login_required` decorators on all API endpoints.
      * Strict user-ownership validation before modifying any object.
  * **Timezone Aware:** Configured for `America/Mexico_City` (or your local timezone) to prevent UTC scheduling conflicts.



