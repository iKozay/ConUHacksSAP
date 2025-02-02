from django.shortcuts import render
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.algorithms import GREEDY_COST, optimize
from .models import CurrentFireEvents, Resource
from rest_framework.parsers import FileUploadParser
import csv
import io

# Serializer for FireEvent model
class FireEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentFireEvents
        fields = ['timestamp', 'fire_start_time', 'latitude', 'longitude', 'severity', 'damage_costs']

# Serializer for Resource model
class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['name', 'deployment_time_hr', 'cost_per_operation', 'units_available']

# API view to get all fire events in JSON format
@api_view(['GET'])
def get_fire_events(request):
    """
    Fetch all fire events from the database and return as JSON
    """
    fire_events = CurrentFireEvents.objects.all()
    serializer = FireEventSerializer(fire_events, many=True)
    return Response(serializer.data)

# API view to get all resources in JSON format
@api_view(['GET'])
def get_resources(request):
    """
    Fetch all resources from the database and return as JSON
    """
    resources = Resource.objects.all()
    serializer = ResourceSerializer(resources, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def optimize_resources(request):
    """
    Optimize resources for fire events
    """
    # Fetch all fire events from the database
    fire_events = CurrentFireEvents.objects.all()

    # Define algorithm
    algorithm = request.query_params.get('algo', GREEDY_COST)

    return Response(generateReport(fire_events, algorithm))

def generateReport(wildfires, algorithm):
    # Define resources
    resources = Resource.objects.all()

    # Track deployed resources and missed fires
    deployed = []
    missed = []
    operational_cost = 0
    damage_cost = 0

    deployed, missed, operational_cost, damage_cost = optimize(wildfires, resources, algorithm)

    # Generate report
    report = {
        'addressed': len(deployed),
        'missed': len(missed),
        'operational_cost': operational_cost,
        'damage_cost': damage_cost,
        'severity_report': {
            'low': CurrentFireEvents.objects.filter(severity='low').count(),
            'medium': CurrentFireEvents.objects.filter(severity='medium').count(),
            'high': CurrentFireEvents.objects.filter(severity='high').count(),
        },
        'deployed_resources_details': [
            {
            'resource_name': resource.name,
            'deployed_time': resource.assigned_time,
            'location': {
                'latitude': event.latitude,
                'longitude': event.longitude
            }
            } for event, resource in deployed
        ],
        'missed_fires_details': [
            {
            'severity': event.severity,
            'location': {
                'latitude': event.latitude,
                'longitude': event.longitude
            }
            } for event in missed
        ]
    }
    return report
