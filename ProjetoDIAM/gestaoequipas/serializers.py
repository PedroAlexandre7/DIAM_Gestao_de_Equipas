from rest_framework import serializers
from .models import Equipa, Treinador, Atleta


class EquipaSerializer(serializers.ModelSerializer): #Acho que n precisamos deste
    class Meta:
        model = Equipa
        fields = ('pk', 'nome_equipa', 'sigla_equipa', 'data_criacao', 'emblema_clube')


class TreinadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treinador
        fields = ('evento', 'response_texto', 'votos')


class AtletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atleta
        fields = ('user', 'equipa', 'foto_perfil')


