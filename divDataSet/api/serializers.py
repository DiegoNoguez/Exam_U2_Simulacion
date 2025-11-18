from django_restframework import serializers


class DatasetUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    use_sample = serializers.BooleanField(default=False)

class SplitParametersSerializer(serializers.Serializer):
    test_size = serializers.FloatField(default=0.4, min_value=0.1, max_value=0.5)
    val_size = serializers.FloatField(default=0.5, min_value=0.1, max_value=0.5)
    random_state = serializers.IntegerField(default=42)
    shuffle = serializers.BooleanField(default=True)
    stratify = serializers.CharField(required=False, allow_blank=True)

class DatasetInfoSerializer(serializers.Serializer):
    total_records = serializers.IntegerField()
    columns_count = serializers.IntegerField()
    columns = serializers.ListField(child=serializers.CharField())
    column_types = serializers.DictField()
    numeric_columns = serializers.ListField(child=serializers.CharField())
    categorical_columns = serializers.ListField(child=serializers.CharField())
    memory_usage_mb = serializers.FloatField()