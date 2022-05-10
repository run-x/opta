from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets

from . import models, serializer


# Create your views here.
def crud_index(request):
    return HttpResponse("Hello, world. You're at the CRUD index.")


class TestModelViewSet(viewsets.ModelViewSet):
    queryset = models.TestModel.objects.all()
    serializer_class = serializer.TestModelSerializer
