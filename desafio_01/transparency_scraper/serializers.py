from rest_framework import serializers

class ScrapeRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True, max_length=100)
    search_filter = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate_search_filter(self, value):
        allowed_filters = ["Beneficiário de Programa", "Servidor Público Federal", ""] # Empty string if not provided
        if value and value not in allowed_filters:
            pass
        return value