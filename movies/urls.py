from django.urls import path
from . import views
urlpatterns=[
    # path('', views.home, name='home'),
    path('',views.movie_list,name='movie_list'),

    path('<int:movie_id>/theaters',views.theater_list,name='theater_list'),
    path('theater/<int:theater_id>/seats/book/',views.book_seats,name='book_seats'),
    
    path('checkout/<int:theater_id>/', views.create_checkout_session, name='checkout'),
    path('payment-success/<int:theater_id>/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),


    path('create-checkout-session/<int:theater_id>/', views.create_checkout_session, name='create_checkout_session'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]