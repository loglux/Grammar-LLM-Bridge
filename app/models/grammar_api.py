"""
Pydantic models for LanguageTool-compatible API.
"""
from pydantic import BaseModel, ConfigDict, Field


class Replacement(BaseModel):
    value: str


class RuleCategory(BaseModel):
    id: str
    name: str


class RuleUrl(BaseModel):
    name: str | None = None
    value: str | None = None


class Rule(BaseModel):
    id: str
    description: str
    issueType: str = "grammar"
    category: RuleCategory | None = None
    urls: list[RuleUrl] | None = None


class TypeInfo(BaseModel):
    typeName: str = "Other"


class Context(BaseModel):
    text: str
    offset: int
    length: int


class Match(BaseModel):
    message: str
    shortMessage: str | None = ""
    replacements: list[Replacement]
    offset: int
    length: int
    context: Context
    sentence: str
    type: TypeInfo = TypeInfo()
    rule: Rule
    ignoreForIncompleteSentence: bool = True
    contextForSureMatch: int = -1
    errorText: str | None = None


class Software(BaseModel):
    name: str
    version: str
    buildDate: str
    apiVersion: int
    premium: bool
    premiumHint: str
    status: str


class Warnings(BaseModel):
    incompleteResults: bool


class DetectedLanguage(BaseModel):
    name: str
    code: str
    confidence: float
    source: str | None = None


class LanguageInfo(BaseModel):
    name: str
    code: str
    detectedLanguage: DetectedLanguage


class DetectedLanguageRate(BaseModel):
    language: str
    rate: float


class ExtendedSentenceRange(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: int = Field(..., alias="from")
    to: int
    detectedLanguages: list[DetectedLanguageRate]


class LTResponse(BaseModel):
    software: Software
    warnings: Warnings
    language: LanguageInfo
    matches: list[Match]
    sentenceRanges: list[list[int]]
    extendedSentenceRanges: list[ExtendedSentenceRange]


class CheckRequest(BaseModel):
    """
    Request payload for /v2/check.
    Permissive to stay backward-compatible with plugins that may send extra fields.
    """

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    language: str | None = "en-GB"
    data: str | dict | None = None
    enabledRules: str | None = None
