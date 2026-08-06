"""認証APIで受け取る入力値の検証をまとめるシリアライザー。"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from api.models import Account


User = get_user_model()


class SignupSerializer(serializers.Serializer):
    """一般ユーザーとAccountを作成する4項目を検証する。"""

    account_number = serializers.CharField(
        max_length=Account._meta.get_field("account_number").max_length,
        trim_whitespace=True,
        error_messages={
            "required": "口座番号を入力してください。",
            "blank": "口座番号を入力してください。",
            "max_length": "口座番号が長すぎます。",
        },
    )
    user_name = serializers.CharField(
        max_length=Account._meta.get_field("user_name").max_length,
        trim_whitespace=True,
        error_messages={
            "required": "表示名を入力してください。",
            "blank": "表示名を入力してください。",
            "max_length": "表示名は100文字以内にしてください。",
        },
    )
    email = serializers.EmailField(
        max_length=User._meta.get_field("username").max_length,
        trim_whitespace=True,
        error_messages={
            "required": "メールアドレスを入力してください。",
            "blank": "メールアドレスを入力してください。",
            "invalid": "メールアドレスの形式が正しくありません。",
            "max_length": "メールアドレスが長すぎます。",
        },
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={
            "required": "パスワードを入力してください。",
            "blank": "パスワードを入力してください。",
        },
    )

    def validate_account_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("口座番号は数字のみで入力してください。")
        if len(value) != 7:
            raise serializers.ValidationError("口座番号は7桁で入力してください。")
        if Account.objects.filter(pk=value).exists():
            raise serializers.ValidationError("この口座番号は既に使用されています。")
        return value

    def validate_user_name(self, value):
        if not value:
            raise serializers.ValidationError("表示名を入力してください。")
        return value

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(
                "このメールアドレスは既に使用されています。"
            )
        return normalized_email

    def validate(self, attrs):
        candidate_user = User(
            username=attrs.get("email", ""),
            email=attrs.get("email", ""),
        )
        try:
            validate_password(attrs["password"], user=candidate_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs
