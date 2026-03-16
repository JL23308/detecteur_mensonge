from rest_framework import serializers
from api.models import Measure

class MeasureSerializer(serializers.ModelSerializer):
    """
    Serializer for heart rate and lie detection points.
    """
    class Meta:
        model = Measure
        fields = '__all__'
        read_only_fields = ('timestamp',)
