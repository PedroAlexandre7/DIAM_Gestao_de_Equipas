from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import generic

from .models import Evento, Resposta, Atleta, Treinador, Equipa, RespostaPossivel
from .calendar_utils import Calendar
from .serializers import *

from rest_framework.decorators import api_view


def index(request):
    latest_event_list = Evento.objects.order_by('-pub_data_evento')[:5]
    context = {'latest_event_list': latest_event_list}
    return render(request, 'gestaoequipas/index.html', context)


def info_equipa(request):  # ver atletas e treinador e apagar
    if request.method == 'POST':
        equipa = Equipa.objects.get(pk=request.POST['equipa_id'])
        equipa.delete()
        return render(request, 'gestaoequipas/index.html')
    else:
        if hasattr(request.user, 'atleta') and request.user.atleta.equipa is not None:
            equipa = request.user.atleta.equipa
            atletas = equipa.atletas.all()
            return render(request, 'gestaoequipas/info_equipa.html', {'equipa': equipa, 'atletas': atletas})
        elif hasattr(request.user, 'treinador') and request.user.treinador.equipa is not None:
            equipa = request.user.treinador.equipa
            atletas = equipa.atletas.all()
            return render(request, 'gestaoequipas/info_equipa.html', {'equipa': equipa, 'atletas': atletas})
        return HttpResponseRedirect(reverse('gestaoequipas:index'))


@permission_required('gestaoequipas.write_delete_alocacao_eventos')
def criarevento(request):
    if request.method == 'POST':
        try:
            tipo_evento = request.POST.get("tipo_evento")
            data_evento = request.POST.get("data_evento")
            local_evento = request.POST.get("local_evento")
            descricao_evento = request.POST.get("descricao_evento")
            equipas = request.POST.getlist("equipas")
        except KeyError:
            return render(request, 'gestaoequipas/criarevento.html')
        if tipo_evento and data_evento and local_evento and descricao_evento and equipas:
            if len(equipas) > 0:
                evento = Evento(tipo_evento=tipo_evento, pub_data_evento=timezone.now(),
                                data_evento=data_evento,
                                local_evento=local_evento, descricao_evento=descricao_evento, num_equipas=len(equipas))
                evento.save()

                for equipa_id in equipas:
                    equipa = Equipa.objects.get(id=equipa_id)
                    evento.equipas.add(equipa)

                evento.save()
            return HttpResponseRedirect(reverse('gestaoequipas:index'))
        else:
            erro = "O evento deve ter pelo menos uma equipa."
            return HttpResponseRedirect(reverse('gestaoequipas:criarevento', args=(erro,)))
    else:
        equipas = Equipa.objects.all()
        return render(request, 'gestaoequipas/criarevento.html', {'equipas': equipas})


@login_required()
def modificarevento(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    request.user.get_user_permissions()
    if request.method == 'POST':
        try:
            resposta_selecionada = RespostaPossivel.objects.get(pk=request.POST['resposta'])

        except KeyError:
            respostas_possiveis = RespostaPossivel.objects.all()
            respostas = Resposta.objects.filter(evento=evento)
            equipas = evento.equipas.all()
            return render(request, 'gestaoequipas/modificarevento.html',
                          {'evento': evento, 'respostas_possiveis': respostas_possiveis,
                           'equipas': equipas, 'respostas': respostas,
                           'mensagem_de_erro': "Não foi selecionada nenhuma resposta"})
        if resposta_selecionada:
            if len(Resposta.objects.filter(evento=evento, atleta=request.user.atleta).all()) > 0:
                resposta = Resposta.objects.get(evento=evento, atleta=request.user.atleta)
                resposta.response = resposta_selecionada
                resposta.save()
            else:
                resposta = Resposta(evento=evento, atleta=request.user.atleta, response=resposta_selecionada)
                resposta.save()
        return HttpResponseRedirect(reverse('gestaoequipas:index'))

    respostas_possiveis = RespostaPossivel.objects.all()
    equipas = evento.equipas.all()
    respostas = Resposta.objects.filter(evento=evento)
    atletas_confirmados = []
    for resposta in respostas:
        if resposta.response.id == 1:
            atletas_confirmados.append(resposta.atleta)
    return render(request, 'gestaoequipas/modificarevento.html',
                  {'evento': evento, 'respostas_possiveis': respostas_possiveis,
                   'equipas': equipas, 'respostas': respostas, 'atletas_confirmados': atletas_confirmados})


@permission_required('gestaoequipas.write_delete_alocacao_eventos')
def apagar_evento(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    evento.delete()
    return HttpResponseRedirect(reverse('gestaoequipas:index'))


def criarequipa(request):
    if request.method == 'POST':
        nome_equipa = request.POST.get("nome_equipa")
        sigla_equipa = request.POST.get("sigla_equipa")
        if nome_equipa and sigla_equipa:
            equipa = Equipa(nome_equipa=nome_equipa, data_criacao=timezone.now(),
                            sigla_equipa=sigla_equipa)
            equipa.save()
            request.user.treinador.equipa = equipa
            request.user.treinador.save()
        return HttpResponseRedirect(reverse('gestaoequipas:index'))
    return render(request, 'gestaoequipas/criarequipa.html')


@login_required
def alterar_emblema(request, equipa_id):
    equipa = get_object_or_404(Equipa, pk=equipa_id)
    if request.method == 'POST':
        try:
            myfile = request.FILES['myfile']
            fs = FileSystemStorage()
            novo_nome = f"e{request.user.id}.jpg"
            if fs.exists(novo_nome):
                fs.delete(novo_nome)
            filename = fs.save(novo_nome, myfile)
            # uploaded_file_url = fs.url(filename)
            equipa.emblema_clube = novo_nome
            equipa.save()
            return render(request, 'gestaoequipas/alterar_emblema.html', {'uploaded_file_url': filename, 'equipa':equipa})
        except KeyError:
            return render(request, 'gestaoequipas/alterar_emblema.html', {'error_message': "Não selecionou um ficheiro", 'equipa':equipa})

    return render(request, 'gestaoequipas/alterar_emblema.html', {'equipa':equipa})


@login_required()
def sair_equipa(request):
    if hasattr(request.user, 'atleta'):
        if request.user.atleta.equipa is not None:
            request.user.atleta.equipa = None
            request.user.atleta.save()
        else:
            equipas = Equipa.objects.all()
            return render(request, 'gestaoequipas/editar_perfil.html', {'equipas': equipas})
    elif hasattr(request.user, 'treinador'):
        if request.user.treinador.equipa is not None:
            request.user.treinador.equipa = None
            request.user.treinador.save()
        else:
            equipas = Equipa.objects.filter(treinador=None)
            return render(request, 'gestaoequipas/editar_perfil.html', {'equipas': equipas})
    return HttpResponseRedirect(reverse('gestaoequipas:perfil'))


# @permission_required('gestaoequipas.write_inscrever_numa_equipa')
# def inscrever_numa_equipa(request, evento_id):
#     response = "Estes sao os resultados do evento %s."
#     return HttpResponse(response % evento_id)


@login_required
def perfil(request):
    return render(request, 'gestaoequipas/perfil.html')

@login_required
def oral(request):
    return render(request, 'gestaoequipas/oral.html')


def loginpage(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            pass_utilizador = request.POST.get('pass_utilizador')
            if username and pass_utilizador:
                user = authenticate(username=username, password=pass_utilizador)
            else:
                error_message = 'Preencha todos os campos'
                context = {'error_message': error_message}
                return render(request, 'gestaoequipas/login.html', context)
        except KeyError:
            return render(request, 'gestaoequipas/index.html', )
        if user is not None:
            if request.user.is_authenticated:
                error_message = 'O utilizador já está autenticado'
                context = {'error_message': error_message}
                return render(request, 'gestaoequipas/login.html', context)
            else:
                login(request, user)
                return HttpResponseRedirect(reverse('gestaoequipas:index'))
        else:
            return render(request, 'gestaoequipas/login.html', {'error_message': 'Utilizador ou password incorretos'})
    else:
        return render(request, 'gestaoequipas/login.html', )


def logoutpage(request):
    logout(request)
    return HttpResponseRedirect(reverse('gestaoequipas:index'))


def criarconta(request):
    if request.method == 'POST':
        pass_utilizador = request.POST['pass_utilizador']
        pass_utilizador_conf = request.POST['pass_utilizador_conf']
        if pass_utilizador_conf != pass_utilizador:
            return render(request, 'gestaoequipas/criarconta.html',
                          {'mensagem_de_erro': "As passwords não correspondem!"})
        utilizador = User.objects.create_user(request.POST['username'], request.POST['mail_utilizador'],
                                              pass_utilizador)
        utilizador.first_name = request.POST['primeiro_nome']
        utilizador.last_name = request.POST['ultimo_nome']
        utilizador.save()
        if request.POST['tipo_utilizador'] == "atleta":
            criar_atleta(utilizador)
        elif request.POST['tipo_utilizador'] == "treinador":
            criar_treinador(utilizador)
        if utilizador is not None:
            login(request, utilizador)
            return HttpResponseRedirect(reverse('gestaoequipas:index'))
        else:
            return render(request, 'gestaoequipas/criarconta.html',
                          {'mensagem_de_erro': "Não foi possível criar conta"})

    return render(request, 'gestaoequipas/criarconta.html', )


def criar_atleta(utilizador):
    atleta = Atleta(user=utilizador)
    atleta.save()
    conteudo = ContentType.objects.get_for_model(Equipa)
    permissoes = [Permission.objects.get(content_type=conteudo, codename='write_inscrever_numa_equipa')]
    conteudo = ContentType.objects.get_for_model(Resposta)
    permissoes.append(Permission.objects.get(content_type=conteudo, codename='read_write_confirmar_presenca'))
    utilizador.user_permissions.add(*permissoes)


def criar_treinador(utilizador):
    treinador = Treinador(user=utilizador)
    treinador.save()
    conteudo = ContentType.objects.get_for_model(Equipa)
    permissoes = [Permission.objects.get(content_type=conteudo, codename='write_inscrever_numa_equipa'),
                  Permission.objects.get(content_type=conteudo, codename='write_delete_Equipa')]
    conteudo = ContentType.objects.get_for_model(Evento)
    permissoes.append(Permission.objects.get(content_type=conteudo, codename='write_delete_alocacao_eventos'))
    utilizador.user_permissions.add(*permissoes)


class CalendarView(generic.ListView):
    model = Evento
    template_name = 'gestaoequipas/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Use today's date or the requested date from the URL
        req_day = self.request.GET.get('day', None)
        d = get_date(req_day)

        # Calculate the previous and next months
        previous_month = d - timedelta(days=1)
        next_month = d + timedelta(days=32)

        # Instantiate our calendar class with the year and month
        cal = Calendar(d.year, d.month)

        # Call the formatmonth method, which returns our calendar as a table
        html_cal = cal.formatmonth(withyear=True)
        context['calendar'] = mark_safe(html_cal)
        context['previous_month'] = previous_month.strftime("%Y-%m-%d")
        context['next_month'] = next_month.strftime("%Y-%m-%d")
        return context


def get_date(req_day):
    if req_day:
        year, month, _ = (int(x) for x in req_day.split('-'))
        return timezone.make_aware(datetime(year, month, day=1))
    return timezone.now().replace(day=1)


@login_required
def fazer_upload(request):
    if request.method == 'POST':
        try:
            myfile = request.FILES['myfile']
            fs = FileSystemStorage()
            novo_nome = f"{request.user.id}.jpg"
            if fs.exists(novo_nome):
                fs.delete(novo_nome)
            filename = fs.save(novo_nome, myfile)
            # uploaded_file_url = fs.url(filename)
            if hasattr(request.user, 'atleta'):
                request.user.atleta.foto_perfil = novo_nome
                request.user.atleta.save()
            else:
                request.user.treinador.foto_perfil = novo_nome
                request.user.treinador.save()
            return render(request, 'gestaoequipas/fazer_upload.html', {'uploaded_file_url': filename})
        except KeyError:
            return render(request, 'gestaoequipas/fazer_upload.html', {'error_message': "Não selecionou um ficheiro", })
    return render(request, 'gestaoequipas/fazer_upload.html')


@login_required
def apagar_perfil(request):
    if request.method == 'POST':
        if hasattr(request.user, 'atleta'):
            request.user.atleta.delete()
        elif hasattr(request.user, 'treinador'):
            request.user.treinador.delete()
        else:
            return HttpResponseRedirect(reverse('gestaoequipas:index'))
        request.user.delete()
        logout(request)
        return HttpResponseRedirect(reverse('gestaoequipas:index'))
    else:
        return render(request, 'gestaoequipas/apagarperfil.html')


@login_required
def editar_perfil(request):
    if request.method == 'POST':
        equipa_pedida = request.POST['equipa']
        equipa = Equipa.objects.get(pk=equipa_pedida)
        if hasattr(request.user, 'atleta'):
            request.user.atleta.equipa = equipa
            request.user.atleta.save()
        elif hasattr(request.user, 'treinador'):
            request.user.treinador.equipa = equipa
            request.user.treinador.save()
        return HttpResponseRedirect(reverse('gestaoequipas:perfil'))
    if hasattr(request.user, 'treinador'):
        equipas = Equipa.objects.filter(treinador=None)
    else:
        equipas = Equipa.objects.all()
    return render(request, 'gestaoequipas/editar_perfil.html', {'equipas': equipas})


@api_view(['GET', 'PUT'])
def ver_perfil(request):
    if request.method == 'GET':
        print(request.user)
        if isinstance(request.user, Atleta):
            profile = Atleta.objects.get(user=request.user)
            serializer = AtletaSerializer(profile)
            return Resposta(serializer.data)
        elif isinstance(request.user, Treinador):  # Verifica se é treinador
            profile = Treinador.objects.get(user=request.user)
            serializer = TreinadorSerializer(profile)
            return Resposta(serializer.data)
        else:
            profile = None
            serializer = TreinadorSerializer(profile)
            return Resposta(serializer.data)
