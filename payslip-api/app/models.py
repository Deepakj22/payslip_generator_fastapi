
from decimal import Decimal
from typing import Annotated
from pydantic import Field, computed_field, model_validator
from pydantic import (
    AliasGenerator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    computed_field,
)
from pydantic.alias_generators import to_camel


Money = Annotated[
    Decimal,
    Field(ge=0, max_digits=12, decimal_places=2),
]

RequiredText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class ApiModel(BaseModel):
    # Accept both .NET-style camelCase and Python snake_case JSON.
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=to_camel,
        ),
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class CompanyDetails(ApiModel):
    company_name: str = ""
    address: str = ""
    gstin: str = ""
    llpin: str = ""
    contact_number: str | None = None
    email: str | None = None
    website: str | None = None


class EmployeeDetails(ApiModel):
    employee_name: RequiredText
    designation: RequiredText
    income_tax_pan: str = Field(
        default="",
        validation_alias="incomeTaxPAN",
        serialization_alias="incomeTaxPAN",
    )


class PayslipRequest(ApiModel):
    company: CompanyDetails = Field(
        default_factory=CompanyDetails
    )
    employee: EmployeeDetails

    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)

   # User supplies only gross pay and profession tax.
    gross_pay: Money
    profession_tax: Money = Decimal("200.00")

    @computed_field
    @property
    def basic_pay(self) -> Decimal:
        return self.gross_pay * Decimal("0.70")

    @computed_field
    @property
    def house_rent_allowance(self) -> Decimal:
        return Decimal("0.00")

    @computed_field
    @property
    def special_allowance(self) -> Decimal:
        return self.gross_pay * Decimal("0.15")

    @computed_field
    @property
    def conveyance_allowance(self) -> Decimal:
        return self.gross_pay * Decimal("0.09")

    @computed_field
    @property
    def fuel_allowance(self) -> Decimal:
        return self.gross_pay * Decimal("0.06")

    @computed_field
    @property
    def total_deductions(self) -> Decimal:
        return self.profession_tax

    @computed_field
    @property
    def net_pay(self) -> Decimal:
        return self.gross_pay - self.total_deductions

    @model_validator(mode="after")
    def validate_net_pay(self):
        if self.net_pay < 0:
            raise ValueError(
                "Deductions cannot exceed gross pay."
            )
        return self
