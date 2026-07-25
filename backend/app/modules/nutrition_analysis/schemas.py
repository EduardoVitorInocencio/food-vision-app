"""Food analysis schemas."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SchemaModel(BaseModel):
    """Strict base model for finite nutritional values."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ConfidenceLevel(StrEnum):
    """Confidence level for food analysis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DetectionType(StrEnum):
    """Detection type for food analysis."""

    visible = "visible"
    inferred = "inferred"


class CalorieRange(SchemaModel):
    """Calorie range for food analysis."""

    min: float | None = Field(default=None, ge=0)
    max: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> "CalorieRange":
        """Ensure the minimum does not exceed the maximum."""

        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min não pode ser maior que max.")
        return self


class NutritionEstimate(SchemaModel):
    """Estimated calories and nutrients for a component or full meal."""

    calories: float | None = Field(default=None, ge=0)
    protein_g: float | None = Field(default=None, ge=0)
    carbohydrates_g: float | None = Field(default=None, ge=0)
    fat_g: float | None = Field(default=None, ge=0)
    fiber_g: float | None = Field(default=None, ge=0)
    sugar_g: float | None = Field(default=None, ge=0)
    sodium_mg: float | None = Field(default=None, ge=0)


class IngredientEstimate(SchemaModel):
    """Visible or inferred ingredient with quantity and confidence."""

    name: str
    detection_type: DetectionType
    estimated_quantity: str | None = None
    estimated_weight_g: float | None = Field(default=None, ge=0)
    estimated_calories: float | None = Field(default=None, ge=0)
    confidence: ConfidenceLevel


class FoodComponent(SchemaModel):
    """One independently described food component in a meal."""

    name: str
    description: str
    estimated_portion: str | None = None
    estimated_weight_g: float | None = Field(default=None, ge=0)
    ingredients: list[IngredientEstimate]
    nutrition: NutritionEstimate
    confidence: ConfidenceLevel


class FoodAnalysis(SchemaModel):
    """Validated structured output for a complete food-image analysis."""

    dish_name: str
    description: str
    components: list[FoodComponent]

    total_nutrition: NutritionEstimate
    total_calorie_range: CalorieRange

    confidence: ConfidenceLevel
    assumptions: list[str]
    warnings: list[str]

    requires_user_confirmation: bool
    follow_up_questions: list[str]

    @model_validator(mode="after")
    def validate_total_calories(self) -> "FoodAnalysis":
        """Ensure total calories remain inside the declared range."""

        calories = self.total_nutrition.calories
        lower = self.total_calorie_range.min
        upper = self.total_calorie_range.max

        if calories is not None and lower is not None and calories < lower:
            raise ValueError("calories não pode ser menor que a faixa mínima.")
        if calories is not None and upper is not None and calories > upper:
            raise ValueError("calories não pode ser maior que a faixa máxima.")
        return self
