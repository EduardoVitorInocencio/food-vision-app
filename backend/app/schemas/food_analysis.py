"""Food analysis schemas."""

from enum import Enum
from pydantic import BaseModel, Field

class ConfidenceLevel(str, Enum):
    """Confidence level for food analysis."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class DetectionType(str, Enum):
    """Detection type for food analysis."""

    visible = "visible"
    inferred = "inferred"

class CalorieRange(BaseModel):
    """Calorie range for food analysis."""

    min: float | None = Field(default=None, ge=0)
    max: float | None = Field(default=None, ge=0)

class NutritionEstimate(BaseModel):
    calories: float | None = Field(default=None, ge=0)
    protein_g: float | None = Field(default=None, ge=0)
    carbohydrates_g: float | None = Field(default=None, ge=0)
    fat_g: float | None = Field(default=None, ge=0)
    fiber_g: float | None = Field(default=None, ge=0)
    sugar_g: float | None = Field(default=None, ge=0)
    sodium_mg: float | None = Field(default=None, ge=0)


class IngredientEstimate(BaseModel):
    name: str
    detection_type: DetectionType
    estimated_quantity: str | None = None
    estimated_weight_g: float | None = Field(default=None, ge=0)
    estimated_calories: float | None = Field(default=None, ge=0)
    confidence: ConfidenceLevel


class FoodComponent(BaseModel):
    name: str
    description: str
    estimated_portion: str | None = None
    estimated_weight_g: float | None = Field(default=None, ge=0)
    ingredients: list[IngredientEstimate]
    nutrition: NutritionEstimate
    confidence: ConfidenceLevel


class FoodAnalysis(BaseModel):
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