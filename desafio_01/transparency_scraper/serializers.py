from rest_framework import serializers


class ScrapeRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    search_filter = serializers.CharField(required=False)
