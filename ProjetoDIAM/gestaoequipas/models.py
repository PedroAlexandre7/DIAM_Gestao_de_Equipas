# Create your models here.

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

import datetime


class Equipa(models.Model):
    nome_equipa = models.CharField(max_length=200)
    sigla_equipa = models.CharField(max_length=5)
    data_criacao = models.DateTimeField('data de criacao')
    emblema_clube = models.CharField(max_length=50, default='default_emblem.png')

    def delete(self, *args, **kwargs):
        eventos_to_delete = Evento.objects.filter(equipa=self, num_equipas=1)
        eventos_to_delete.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.nome_equipa

    class Meta:
        permissions = (("write_inscrever_numa_equipa", "o utilizador pode inscrever e desinscrever-se numa equipa"),
                       ("write_delete_Equipa", "o utilizador pode criar equipas, apagar equipas e remover atletas da "
                                               "equipa"),)


class Evento(models.Model):
    equipas = models.ManyToManyField(Equipa)
    tipo_evento = models.CharField(max_length=200)
    pub_data_evento = models.DateTimeField('data de publicacao')
    data_evento = models.DateTimeField('data do evento')
    local_evento = models.CharField(max_length=300)
    descricao_evento = models.CharField(max_length=500)
    num_equipas = models.IntegerField(default=1)

    def foi_publicado_recentemente(self):
        return self.pub_data_evento >= timezone.now() - datetime.timedelta(days=1)

    def __str__(self):
        return self.descricao_evento

    class Meta:
        permissions = (("write_delete_alocacao_eventos", "o utilizador pode criar eventos, apagar eventos e inscrever "
                                                         "em eventos"),)


class Atleta(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    equipa = models.ForeignKey(Equipa, on_delete=models.SET_NULL, null=True,
                               related_name='atletas')  # com related_name posso fazer equipa.atletas.all()
    foto_perfil = models.CharField(max_length=50, default='default.png')


class RespostaPossivel(models.Model):
    respostaPossivel = models.CharField(max_length=50)


class Resposta(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE)
    response = models.ForeignKey(RespostaPossivel, on_delete=models.SET_NULL, null=True, default=0)

    def __str__(self):
        return self.response

    class Meta:
        permissions = (("read_write_confirmar_presenca", "o utilizador pode confirmar presença num evento"),)


class Treinador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    equipa = models.OneToOneField(Equipa, on_delete=models.SET_NULL, null=True)
    foto_perfil = models.CharField(max_length=50, default='default.png')
