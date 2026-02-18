🎬 Django BookMyShow Clone – Movie Ticket Booking System
📌 Project Overview

This project is a full-stack web-based Movie Ticket Booking System developed using Django. It allows users to browse movies, select theaters, choose seats, make secure online payments, and receive booking confirmation emails. The system also includes an admin analytics dashboard for monitoring revenue and booking statistics.

This project simulates real-world movie ticket booking platforms and demonstrates practical implementation of authentication, payment gateway integration, and seat reservation management.

🚀 Features Implemented
✅ User Features
🎥 Movie Browsing

View available movies.

View movie details including:

Movie description.

Cast information.

Ratings

Trailer videos

🎭 Genre and Language Filters

Users can filter movies based on:

Genre (Action, Comedy, Drama, Horror).

Language (Hindi, English, Tamil, Telugu).

This improves search efficiency and user experience.

🎟 Seat Selection System

Interactive seat selection.

Shows available and booked seats.

Prevents double booking.

⏳ Seat Reservation Timeout

Seats are temporarily reserved for 5 minutes.

Automatically released if payment is not completed.

Prevents seat blocking and improves fairness.

💳 Online Payment Integration:(using stripe in test mode)

Secure payment processing.

Supports card payments.

Payment success and cancellation handling.

Booking confirmation only after successful payment.

📧 Email Ticket Confirmation

After successful booking:

User receives email confirmation.

Email contains:

Movie Name.

Theater Name.

Seat Numbers.

Show Timing.

▶ Movie Trailer Integration

YouTube trailers Link.

Helps users decide before booking.

✅ Admin Features
📊 Admin Analytics Dashboard

Admin can monitor:

Total Revenue Generated.

Most Popular Movies.

Busiest Theaters.