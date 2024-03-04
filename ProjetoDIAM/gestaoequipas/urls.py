from django.urls import include, path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'gestaoequipas'
urlpatterns = [
    path("", views.CalendarView.as_view(), name="index"),

    path('criarconta', views.criarconta, name='criarconta'),
    path('login', views.loginpage, name="loginpage"),
    path('login', auth_views.LoginView.as_view()),
    path('perfil', views.perfil, name='perfil'),
    path('apagarperfil', views.apagar_perfil, name='apagar_perfil'),
    path('editar_perfil', views.editar_perfil, name='editar_perfil'),
    path('fazer_upload', views.fazer_upload, name='fazer_upload'),
    path('logout', views.logoutpage, name='logout'),
    path('oral', views.oral, name='oral'),

    path('criarequipa', views.criarequipa, name='criarequipa'),
    path('<int:equipa_id>/alterar_emblema', views.alterar_emblema, name='alterar_emblema'),
    path('sair_equipa', views.sair_equipa, name='sair_equipa'),
    path('info_equipa', views.info_equipa, name='info_equipa'),

    path('criarevento', views.criarevento, name='criarevento'),
    path('<int:evento_id>', views.modificarevento, name='modificarevento'),
    path('<int:evento_id>/apagar_evento', views.apagar_evento, name='apagar_evento'),


    #path('api/ver_perfil/', views.ver_perfil),
    #path('api/fazer_upload', views.fazer_upload),

]

