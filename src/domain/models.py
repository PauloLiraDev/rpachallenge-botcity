"""Modelos de dados que cruzam fronteiras do processo."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Person(BaseModel):
    """Uma linha da planilha do desafio."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    company_name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    address: str = Field(min_length=1)
    email: str = Field(min_length=3, pattern=r"^[^@\s]+@[^@\s]+$")
    phone: str = Field(min_length=1)

    @field_validator("phone", mode="before")
    @classmethod
    def _phone_as_text(cls, value: object) -> object:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, int):
            return str(value)
        return value


class ChallengeResult(BaseModel):
    """Resultado exibido pelo site ao fim das 10 rodadas."""

    success_rate: int = Field(ge=0, le=100)
    correct_fields: int = Field(ge=0)
    total_fields: int = Field(ge=0)
    elapsed_ms: int = Field(ge=0)
    message: str
