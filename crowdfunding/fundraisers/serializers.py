from rest_framework import serializers
from .models import Fundraiser, Pledge


class FundraiserSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
    supporters = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Fundraiser
        fields = '__all__'


class PledgeSerializer(serializers.ModelSerializer):
    supporter = serializers.ReadOnlyField(source='supporter.id')

    class Meta:
        model = Pledge
        fields = ['id', 'supporter', 'type', 'hours', 'action', 'comment', 'created_at', 'fundraiser']
        read_only_fields = ['id', 'supporter', 'created_at']

    def validate(self, data):
        
        pledge_type = data.get('type')

        if pledge_type is None and self.instance:
            pledge_type = self.instance.type

        if pledge_type == 'time':
            hours = data.get('hours')
            if hours in (None, ''):
                raise serializers.ValidationError({"hours": "You must provide hours for a time pledge."})
            if hours <= 0:
                raise serializers.ValidationError({"hours": "Hours must be greater than 0."})
            if hours > 4:
                raise serializers.ValidationError({"hours": "Maximum allowed is 4 hours."})

        elif pledge_type == 'words':
            action = data.get('action')
            if not action:
                raise serializers.ValidationError({"action": "You must provide an action for a words pledge."})

        else:
            raise serializers.ValidationError({"type": "Invalid pledge type."})

        return data

    def create(self, validated_data):
        
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['supporter'] = request.user
        return super().create(validated_data)


class FundraiserDetailSerializer(FundraiserSerializer):
    pledges = PledgeSerializer(many=True, read_only=True)

class InvitationSerializer(serializers.Serializer):
    user = serializers.IntegerField()
    fundraiser = serializers.IntegerField()
