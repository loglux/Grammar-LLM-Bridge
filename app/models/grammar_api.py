"""
Pydantic models for LanguageTool-compatible API.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Union


class Replacement(BaseModel):
    value: str


class RuleCategory(BaseModel):
    id: str
    name: str


class RuleUrl(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class Rule(BaseModel):
    id: str
    description: str
    issueType: str = "grammar"
    category: Optional[RuleCategory] = None
    urls: Optional[List[RuleUrl]] = None


class TypeInfo(BaseModel):
    typeName: str = "Other"


class Context(BaseModel):
    text: str
    offset: int
    length: int


class Match(BaseModel):
    message: str
    shortMessage: Optional[str] = ""
    replacements: List[Replacement]
    offset: int
    length: int
    context: Context
    sentence: str
    type: TypeInfo = TypeInfo()
    rule: Rule
    ignoreForIncompleteSentence: bool = True
    contextForSureMatch: int = -1
    errorText: Optional[str] = None


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
    source: Optional[str] = None


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
    detectedLanguages: List[DetectedLanguageRate]


class LTResponse(BaseModel):
    software: Software
    warnings: Warnings
    language: LanguageInfo
    matches: List[Match]
    sentenceRanges: List[List[int]]
    extendedSentenceRanges: List[ExtendedSentenceRange]


class CheckRequest(BaseModel):
    """
    Request payload for /v2/check.
    Permissive to stay backward-compatible with plugins that may send extra fields.
    """

    model_config = ConfigDict(extra="allow")

    text: Optional[str] = None
    language: Optional[str] = "en-GB"
    data: Optional[Union[str, dict]] = None
    enabledRules: Optional[str] = None
