# from django.shortcuts import render, redirect ,get_object_or_404
# from .models import Movie,Theater,Seat,Booking
# from django.contrib.auth.decorators import login_required
# from django.db import IntegrityError

# from django.shortcuts import render
# from .models import Movie

# from django.core.mail import send_mail
# from django.conf import settings

# import stripe
# from django.conf import settings
# from django.urls import reverse

# stripe.api_key = settings.STRIPE_SECRET_KEY


# def movie_list(request):
#     movies = Movie.objects.all()

#     genre = request.GET.get('genre')
#     language = request.GET.get('language')

#     if genre:
#         movies = movies.filter(genre=genre)

#     if language:
#         movies = movies.filter(language=language)

#     context = {
#         'movies': movies
#     }
#     return render(request, 'movies/movie_list.html', context)

# def theater_list(request,movie_id):
#     movie = get_object_or_404(Movie, id=movie_id)
#     theaters=Theater.objects.filter(movie=movie)
#     return render(request,'movies/theater_list.html',{
#         'movie':movie,
#         'theaters':theaters
#         })



# @login_required(login_url='/login/')
# def book_seats(request,theater_id):
#     theaters=get_object_or_404(Theater,id=theater_id)
#     seats=Seat.objects.filter(theater=theaters)
#     if request.method=='POST':
#         selected_Seats= request.POST.getlist('seats')
#         error_seats=[]
#         if not selected_Seats:
#             return render(request,"movies/seat_selection.html",{'theater':theaters,"seats":seats,'error':"No seat selected"})
#         for seat_id in selected_Seats:
#             seat=get_object_or_404(Seat,id=seat_id,theater=theaters)
#             if seat.is_booked:
#                 error_seats.append(seat.seat_number)
#                 continue
#             try:
#                 Booking.objects.create(
#                     user=request.user,
#                     seat=seat,
#                     movie=theaters.movie,
#                     theater=theaters
#                 )
#                 seat.is_booked=True
#                 seat.save()
#             except IntegrityError:
#                 error_seats.append(seat.seat_number)
#         if error_seats:
#             error_message=f"The following seats are already booked:{','.join(error_seats)}"
#             return render(request,'movies/seat_selection.html',{'theater':theaters,"seats":seats,'error':"No seat selected"})
#         seat_numbers = [Seat.objects.get(id=s).seat_number for s in selected_Seats]

#         subject = "Booking Confirmation - BookMySeat"
#         message = f"""
# Hello {request.user.username},

# Your booking is confirmed 🎉

# Movie: {theaters.movie.name}
# Theater: {theaters.name}
# Seats: {', '.join(seat_numbers)}
# Show Time: {theaters.time}

# Enjoy your movie 🍿
# """
#         recipient_list = [request.user.email]

#         # Send email
#         send_mail(
#             subject,
#             message,
#             settings.EMAIL_HOST_USER,
#             recipient_list,
#             fail_silently=False,
# )
   
#         return redirect('profile')
#     return render(request,'movies/seat_selection.html',{'theater':theaters,"seats":seats})




# @login_required
# def create_checkout_session(request, theater_id):

#     theater = get_object_or_404(Theater, id=theater_id)

#     session = stripe.checkout.Session.create(
#         payment_method_types=['card'],
#         line_items=[{
#             'price_data': {
#                 'currency': 'inr',
#                 'product_data': {
#                     'name': theater.movie.name,
#                 },
#                 'unit_amount': int(theater.price * 100),
#             },
#             'quantity': 1,
#         }],
#         mode='payment',
#         success_url=request.build_absolute_uri(
#             reverse('payment_success', args=[theater.id])
#         ),
#         cancel_url=request.build_absolute_uri(
#             reverse('payment_cancel')
#         ),
#     )

#     return redirect(session.url, code=303)


# @login_required
# def payment_success(request, theater_id):

#     theater = get_object_or_404(Theater, id=theater_id)

#     return render(request, "movies/payment_success.html", {"theater": theater})



# @login_required
# def payment_cancel(request):
#     return render(request, "movies/payment_cancel.html")





from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from .models import Booking, Movie, Theater

import stripe

from django.utils import timezone
from datetime import timedelta

from .models import Booking


def release_expired_seats():

    # Release expired temporary reservations
    expired = Booking.objects.filter(
        is_paid=False,
        reserved_at__lt=timezone.now() - timedelta(minutes=5)
    )

    for booking in expired:
        booking.delete()

    # Release seats after show completed
    old_shows = Booking.objects.filter(
        theater__time__lt=timezone.now()
    )

    for booking in old_shows:
        booking.seat.is_booked = False
        booking.seat.save()
        booking.delete()



stripe.api_key = settings.STRIPE_SECRET_KEY


def release_expired_seats():
    expired = Booking.objects.filter(
        is_paid=False,
        reserved_at__lt=timezone.now() - timedelta(minutes=5)
    )

    for booking in expired:
        booking.seat.is_booked = False
        booking.seat.save()
        booking.delete()

def movie_list(request):
    movies = Movie.objects.all()

    genre = request.GET.get('genre')
    language = request.GET.get('language')

    if genre:
        movies = movies.filter(genre=genre)

    if language:
        movies = movies.filter(language=language)

    return render(request, 'movies/movie_list.html', {'movies': movies})


def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)

    return render(request, 'movies/theater_list.html', {
        'movie': movie,
        'theaters': theaters
    })


# ==============================
# SEAT SELECTION (Store seats in session)
# ==============================
@login_required(login_url='/login/')
def book_seats(request, theater_id):

    release_expired_seats() 
    theater = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theater)

    if request.method == 'POST':
        selected_seats = request.POST.getlist('seats')

        if not selected_seats:
            return render(request, "movies/seat_selection.html", {
                'theater': theater,
                "seats": seats,
                'error': "No seat selected"
        })



        available_seats = Seat.objects.filter(
            id__in=selected_seats,
            theater=theater,
            is_booked=False
    )
        


        if len(available_seats) != len(selected_seats):
            return render(request, "movies/seat_selection.html", {
                'theater': theater,
                "seats": seats,
                'error': "Some seats already booked!"
        })
    

        for seat in available_seats:
            Booking.objects.create(
            user=request.user,
            seat=seat,
            movie=theater.movie,
            theater=theater,
            total_price=theater.price
            )


        # available_seats.update(is_booked=True)

        

        # if not selected_seats:
            # return render(request, "movies/seat_selection.html", {
                # 'theater': theater,
                # "seats": seats,
                # 'error': "No seat selected"
            # })

        # Store seats temporarily
        request.session['selected_seats'] = selected_seats

        return redirect('create_checkout_session', theater_id=theater.id)

    return render(request, 'movies/seat_selection.html', {
        'theater': theater,
        "seats": seats
    })


# ==============================
# STRIPE PAYMENT SESSION
# ==============================
@login_required
def create_checkout_session(request, theater_id):

    theater = get_object_or_404(Theater, id=theater_id)
    selected_seats = request.session.get('selected_seats', [])

    if not selected_seats:
        return redirect('book_seats', theater_id=theater.id)
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': theater.movie.name,
                },
                'unit_amount': int(theater.price * 100),
            },
            'quantity': len(selected_seats), 
        }],
        mode='payment',
        success_url=request.build_absolute_uri(
            reverse('payment_success', args=[theater.id])
        ),
        cancel_url=request.build_absolute_uri(
            reverse('payment_cancel')
        ),
    )

    return redirect(session.url, code=303)


# ==============================
# PAYMENT SUCCESS → BOOKING + EMAIL
# ==============================
@login_required
def payment_success(request, theater_id):

    theater = get_object_or_404(Theater, id=theater_id)
    selected_seats = request.session.get('selected_seats', [])

    seat_numbers = []

    for seat_id in selected_seats:
        seat = get_object_or_404(Seat, id=seat_id, theater=theater)




        booking = Booking.objects.filter(
            user=request.user,
            seat=seat,
            is_paid=False
        ).first()

        if booking and booking.is_expired():
            # booking.seat.is_booked = False
            # booking.seat.save()
            booking.delete()
            return HttpResponse("Booking expired. Please try again.")
    
        # if seat.is_booked:
            # continue


        if booking:
            booking.is_paid = True
            booking.save()

            seat.is_booked = True
            seat.save()

        seat_numbers.append(seat.seat_number)




        # Booking.objects.create(
            # user=request.user,
            # seat=seat,
            # movie=theater.movie,
            # theater=theater,
            # is_paid=True
        # )

        # seat.is_booked = True
        # seat.save()

    # Send confirmation email
    subject = "Booking Confirmation - BookMySeat"

    message = f"""
Hello {request.user.username},

Your booking is confirmed 🎉

Movie: {theater.movie.name}
Theater: {theater.name}
Seats: {', '.join(seat_numbers)}
Show Time: {theater.time}

Enjoy your movie 🍿
"""

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [request.user.email],
        fail_silently=False,
    )

    # Clear session
    if 'selected_seats' in request.session:
        del request.session['selected_seats']

    return render(request, "movies/payment_success.html", {"theater": theater})


# ==============================
# PAYMENT CANCEL
# ==============================
# @login_required
# def payment_cancel(request):
    # return render(request, "movies/payment_cancel.html")


@login_required
def payment_cancel(request):

    selected_seats = request.session.get('selected_seats', [])

    for seat_id in selected_seats:
        booking = Booking.objects.filter(
            user=request.user,
            seat_id=seat_id,
            is_paid=False
        ).first()

        # if booking:
            # booking.seat.is_booked = False
            # booking.seat.save()
            # booking.delete()

        if booking:
            booking.delete()

    # Clear session
    if 'selected_seats' in request.session:
        del request.session['selected_seats']

    return render(request, "movies/payment_cancel.html")





@staff_member_required
def admin_dashboard(request):

    # Total Revenue
    total_revenue = Booking.objects.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Most Popular Movies
    popular_movies = (
        Booking.objects.values('movie__name')
        .annotate(total_bookings=Count('id'))
        .order_by('-total_bookings')[:5]
    )

    # Busiest Theaters
    busiest_theaters = (
        Booking.objects.values('theater__name')
        .annotate(total_bookings=Count('id'))
        .order_by('-total_bookings')[:5]
    )

    context = {
        'total_revenue': total_revenue,
        'popular_movies': popular_movies,
        'busiest_theaters': busiest_theaters,
    }

    return render(request, 'movies/admin_dashboard.html', context)











# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Movie, Theater, Seat, Booking
# from django.contrib.auth.decorators import login_required
# from django.core.mail import send_mail
# from django.conf import settings
# from django.urls import reverse
# from django.http import HttpResponse
# import stripe

# from django.utils import timezone
# from datetime import timedelta


# stripe.api_key = settings.STRIPE_SECRET_KEY


# # ==============================
# # RELEASE EXPIRED / OLD BOOKINGS
# # ==============================
# def release_expired_seats():

#     # Release unpaid temporary bookings (5 minutes timeout)
#     expired = Booking.objects.filter(
#         is_paid=False,
#         reserved_at__lt=timezone.now() - timedelta(minutes=5)
#         # booked_at__lt=timezone.now() - timedelta(minutes=5)
#     )

#     for booking in expired:
#         # booking.seat.is_booked = False
#         # booking.seat.save()
#         booking.delete()

#     # Release seats after show time completed
#     old_shows = Booking.objects.filter(
#         theater__time__lt=timezone.now()
#     )

#     for booking in old_shows:
#         booking.seat.is_booked = False
#         booking.seat.save()
#         booking.delete()


# # ==============================
# # MOVIE LIST
# # ==============================
# def movie_list(request):

#     release_expired_seats()

#     movies = Movie.objects.all()

#     genre = request.GET.get('genre')
#     language = request.GET.get('language')

#     if genre:
#         movies = movies.filter(genre=genre)

#     if language:
#         movies = movies.filter(language=language)

#     return render(request, 'movies/movie_list.html', {'movies': movies})


# # ==============================
# # THEATER LIST
# # ==============================
# def theater_list(request, movie_id):

#     release_expired_seats()

#     movie = get_object_or_404(Movie, id=movie_id)
#     theaters = Theater.objects.filter(movie=movie)

#     return render(request, 'movies/theater_list.html', {
#         'movie': movie,
#         'theaters': theaters
#     })


# # ==============================
# # SEAT SELECTION
# # ==============================
# @login_required(login_url='/login/')
# def book_seats(request, theater_id):

#     release_expired_seats()

#     theater = get_object_or_404(Theater, id=theater_id)
#     seats = Seat.objects.filter(theater=theater)

#     if request.method == 'POST':

#         selected_seats = request.POST.getlist('seats')

#         if not selected_seats:
#             return render(request, "movies/seat_selection.html", {
#                 'theater': theater,
#                 "seats": seats,
#                 'error': "No seat selected"
#             })

#         available_seats = Seat.objects.filter(
#             id__in=selected_seats,
#             theater=theater,
#             is_booked=False
#         )

#         if len(available_seats) != len(selected_seats):
#             return render(request, "movies/seat_selection.html", {
#                 'theater': theater,
#                 "seats": seats,
#                 'error': "Some seats already booked!"
#             })

#         # Create temporary reservation
#         for seat in available_seats:
#             Booking.objects.get_or_create(
#                 user=request.user,
#                 seat=seat,
#                 movie=theater.movie,
#                 theater=theater,
#                 is_paid=False
#             )

#         request.session['selected_seats'] = selected_seats

#         return redirect('create_checkout_session', theater_id=theater.id)

#     return render(request, 'movies/seat_selection.html', {
#         'theater': theater,
#         "seats": seats
#     })


# # ==============================
# # STRIPE CHECKOUT
# # ==============================
# @login_required
# def create_checkout_session(request, theater_id):

#     theater = get_object_or_404(Theater, id=theater_id)
#     selected_seats = request.session.get('selected_seats', [])

#     if not selected_seats:
#         return redirect('book_seats', theater_id=theater.id)

#     session = stripe.checkout.Session.create(
#         payment_method_types=['card'],
#         line_items=[{
#             'price_data': {
#                 'currency': 'inr',
#                 'product_data': {
#                     'name': theater.movie.name,
#                 },
#                 'unit_amount': int(theater.price * 100),
#             },
#             'quantity': len(selected_seats),
#         }],
#         mode='payment',
#         success_url=request.build_absolute_uri(
#             reverse('payment_success', args=[theater.id])
#         ),
#         cancel_url=request.build_absolute_uri(
#             reverse('payment_cancel')
#         ),
#     )

#     return redirect(session.url, code=303)


# # ==============================
# # PAYMENT SUCCESS
# # ==============================
# @login_required
# def payment_success(request, theater_id):

#     release_expired_seats()

#     theater = get_object_or_404(Theater, id=theater_id)
#     selected_seats = request.session.get('selected_seats', [])

#     seat_numbers = []

#     for seat_id in selected_seats:

#         seat = get_object_or_404(Seat, id=seat_id, theater=theater)

#         booking = Booking.objects.filter(
#             user=request.user,
#             seat=seat,
#             is_paid=False
#         ).first()

#         if booking and booking.is_expired():
#             booking.delete()
#             return HttpResponse("Booking expired. Please try again.")

#         if booking:
#             booking.is_paid = True
#             booking.save()

#             seat.is_booked = True
#             seat.save()

#             seat_numbers.append(seat.seat_number)

#     # Email confirmation
#     subject = "Booking Confirmation - BookMySeat"

#     message = f"""
# Hello {request.user.username},

# Your booking is confirmed 🎉

# Movie: {theater.movie.name}
# Theater: {theater.name}
# Seats: {', '.join(seat_numbers)}
# Show Time: {theater.time}

# Enjoy your movie 🍿
# """

#     send_mail(
#         subject,
#         message,
#         settings.EMAIL_HOST_USER,
#         [request.user.email],
#         fail_silently=False,
#     )

#     if 'selected_seats' in request.session:
#         del request.session['selected_seats']

#     return render(request, "movies/payment_success.html", {"theater": theater})


# # ==============================
# # PAYMENT CANCEL
# # ==============================
# @login_required
# def payment_cancel(request):

#     selected_seats = request.session.get('selected_seats', [])

#     for seat_id in selected_seats:
#         booking = Booking.objects.filter(
#             user=request.user,
#             seat_id=seat_id,
#             is_paid=False
#         ).first()

#         if booking:
#             booking.delete()

#     if 'selected_seats' in request.session:
#         del request.session['selected_seats']

#     return render(request, "movies/payment_cancel.html")

