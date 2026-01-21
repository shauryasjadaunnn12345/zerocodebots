"""
URL configuration for tanish project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from home import views
from django.conf.urls.static import static
from tanish import settings
from home.views import robots_txt, sitemap_xml
urlpatterns = [
    path('admin/', admin.site.urls),
        path("accounts/", include("allauth.urls")),
    path('',include('home.urls')),
    
     path('dashboard',views.dashboard,name='dashboard'),
     path('create/', views.create_project_view, name='create_project'),
# urls.py
path('project/<int:pk>/edit/', views.edit_project_view, name='edit_project'),
path('project/<int:pk>/import-website/', views.import_from_website, name='import_from_website'),
    path('services/', views.services, name='services'),
    path('features/', views.features, name='features'),
    path('signup/', views.signup_view, name='signup'),
    path('verify/', views.verify_otp_view, name='verify_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot/', views.forgot_password_view, name='forgot_password'),
    path('reset-otp/', views.reset_otp_view, name='reset_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('my-projects/', views.my_projects_view, name='my_projects'),
    path('chatbot/<int:project_id>/', views.chatbot_view, name='chatbot'),
path('ask_bot/<int:project_id>/', views.ask_bot, name='ask_bot'),
path("embed-chatbot/", views.embed_chatbot, name="embed_chatbot"),
path('submit_feedback/<int:project_id>/', views.submit_feedback, name='submit_feedback'),
path('project/<int:pk>/analytics/', views.project_analytics, name='project_analytics'),
path('project/<int:pk>/analytics/export/', views.export_analytics, name='export_analytics'),
path('project/<int:pk>/analytics/dashboard/', views.project_analytics_dashboard, name='project_analytics_dashboard'),
path('project/<int:pk>/debug-qa-match/', views.debug_qa_match, name='debug_qa_match'),
path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap_xml, name='sitemap_xml'),
path('project/<int:pk>/summary/', views.project_summary_view, name='project_summary'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

