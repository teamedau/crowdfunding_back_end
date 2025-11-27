from rest_framework import serializers
from django.apps import apps
from .models import Fundraiser, Pledge

class FundraiserSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
    supporters = serializers.SlugRelatedField(
        many=True, slug_field= 'owner.id', read_only=True
    )
    class Meta:
        model = apps.get_model('fundraisers.Fundraiser')
        fields = '__all__'

class PledgeSerializer(serializers.ModelSerializer):
    supporter = serializers.ReadOnlyField(source='supporter.id')
    class Meta:
        model = apps.get_model('fundraisers.Pledge')
        fields = '__all__'
    def create(self, validated_data):
        request = self.context['request']
        validated_data['supporter'] = request.user
        return super().create(validated_data)

class FundraiserDetailSerializer(FundraiserSerializer):
    pledges = PledgeSerializer(many=True, read_only=True)

def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.goal = validated_data.get('goal', instance.goal)
        instance.image = validated_data.get('image', instance.image)
        instance.is_open = validated_data.get('is_open', instance.is_open)
        instance.date_created = validated_data.get('date_created', instance.date_created)
        instance.owner = validated_data.get('owner', instance.owner)
        instance.save()
        return instance