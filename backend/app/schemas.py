import csv
import io
import json
import re
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

TARGET_TYPES = {"prompt", "agent_http", "rag_http"}
ASSERT_TYPES = {"contains", "regex", "json_valid"}
STATUS_VALUES = {"active", "inactive", "deleted"}
LIST_STATUS_FILTER_VALUES = {"active", "inactive", "deleted", "all"}


class TestTargetCreate(BaseModel):
    name: str
    target_type: Literal["prompt", "agent_http", "rag_http"]
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    method: Optional[str] = "POST"
    headers_json: Optional[str] = None
    body_template: Optional[str] = None
    prompt_content: Optional[str] = None

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: Optional[str]) -> Optional[str]:
        return value.upper() if value else value

    @field_validator("headers_json")
    @classmethod
    def validate_headers_json(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return value
        json.loads(value)
        return value


class TestTargetRead(BaseModel):
    id: int
    name: str
    target_type: str
    description: Optional[str]
    endpoint_url: Optional[str]
    method: Optional[str]
    headers_json: Optional[str]
    body_template: Optional[str]
    prompt_content: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TestSuiteRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    case_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class TestCaseRead(BaseModel):
    id: int
    suite_id: int
    case_id: str
    case_name: str
    input_text: str
    assert_type: str
    expected_value: str

    class Config:
        from_attributes = True


class TestCaseUploadResponse(BaseModel):
    suite_id: int
    case_count: int


class TestRunCreate(BaseModel):
    target_id: int
    suite_id: int


class TestRunRead(BaseModel):
    id: int
    target_id: int
    suite_id: int
    status: str
    total: int
    passed: int
    failed: int
    created_at: datetime

    class Config:
        from_attributes = True


class TestRunCreateResponse(BaseModel):
    run_id: int
    total: int
    passed: int
    failed: int


class TestResultRead(BaseModel):
    id: int
    run_id: int
    case_id: str
    case_name: str
    input_text: str
    actual_output: str
    assert_type: str
    expected_value: str
    passed: bool
    reason: str
    latency_ms: int

    class Config:
        from_attributes = True


class ParsedCsvCase(BaseModel):
    case_id: str
    case_name: str
    input_text: str
    assert_type: Literal["contains", "regex", "json_valid"]
    expected_value: str


class PromptVersionBase(BaseModel):
    prompt_name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    prompt_content: str = Field(..., min_length=1)
    is_baseline: bool = False
    baseline_version_id: Optional[int] = None
    status: str = "draft"
    remark: Optional[str] = None


class PromptVersionCreate(PromptVersionBase):
    pass


class PromptVersionUpdate(PromptVersionBase):
    pass


class PromptVersionRead(PromptVersionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelConfigBase(BaseModel):
    config_name: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    base_url: Optional[str] = None
    model: str = Field(..., min_length=1)
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 2048
    is_default: bool = False
    status: str = "active"
    remark: Optional[str] = None


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    config_name: Optional[str] = Field(None, min_length=1)
    provider: Optional[str] = Field(None, min_length=1)
    base_url: Optional[str] = None
    model: Optional[str] = Field(None, min_length=1)
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class ModelConfigRead(ModelConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in STATUS_VALUES:
            raise ValueError("status must be one of: active, inactive, deleted")
        return value


class PromptRunOnceRequest(BaseModel):
    prompt_version_id: int
    model_config_id: int
    input_text: Optional[str] = None
    input_variables: Optional[Any] = None
    assert_type: Optional[str] = None
    expected_value: Optional[str] = None


class PromptInputSnapshotRead(BaseModel):
    input_text: Optional[str]
    input_variables: Optional[dict]
    rendered_prompt: str


class PromptAssertionRead(BaseModel):
    assert_type: Optional[str]
    expected_value: Optional[str]
    assertion_status: str
    assertion_passed: Optional[bool]
    assertion_reason: str

    class Config:
        from_attributes = True


class PromptTestResultRead(BaseModel):
    id: int
    run_id: int
    repeat_index: int
    actual_output: str
    raw_response: Optional[str]
    error_message: Optional[str]
    duration_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class PromptTestRunRead(BaseModel):
    id: int
    prompt_version_id: int
    model_config_id: int
    input_text: str
    prompt_content_snapshot: str
    model_config_snapshot: str
    repeat_count: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class PromptRunOnceResponse(BaseModel):
    run_id: int
    result_id: int
    status: str
    prompt_version_id: int
    model_config_id: int
    actual_output: str
    duration_ms: int
    error_message: Optional[str]
    assertion: Optional[PromptAssertionRead] = None
    input_snapshot: Optional[PromptInputSnapshotRead] = None


class PromptRepeatResultItem(BaseModel):
    result_id: int
    repeat_index: int
    status: str
    actual_output: str
    duration_ms: int
    error_message: Optional[str]
    assertion: Optional[PromptAssertionRead] = None


class PromptRunRepeatSummary(BaseModel):
    total: int
    success_count: int
    failed_count: int
    assertion_passed_count: int
    assertion_failed_count: int
    assertion_skipped_count: int


class PromptRunRepeatRequest(BaseModel):
    prompt_version_id: int
    model_config_id: int
    input_text: Optional[str] = None
    input_variables: Optional[Any] = None
    assert_type: Optional[str] = None
    expected_value: Optional[str] = None
    repeat_count: int = 3


class PromptRunRepeatResponse(BaseModel):
    run_id: int
    status: str
    prompt_version_id: int
    model_config_id: int
    repeat_count: int
    summary: PromptRunRepeatSummary
    results: list[PromptRepeatResultItem]
    input_snapshot: PromptInputSnapshotRead


class PromptScoreRequest(BaseModel):
    scorer_model_config_id: int
    expected_behavior: Optional[str] = None
    remark: Optional[str] = None


class PromptScoreRead(BaseModel):
    id: int
    run_id: int
    result_id: int
    scorer_model_config_id: int
    scoring_template_id: str
    expected_behavior: Optional[str]
    dimension_scores: Optional[dict]
    total_score: Optional[float]
    score_reason: Optional[str]
    problem_points: Optional[list]
    suggestion: Optional[str]
    raw_response: Optional[str]
    status: str
    error_message: Optional[str]
    duration_ms: int
    remark: Optional[str]
    created_at: datetime


class PromptManualReviewRequest(BaseModel):
    manual_status: str
    manual_remark: Optional[str] = None
    reviewer: Optional[str] = None


class PromptManualReviewRead(BaseModel):
    id: int
    run_id: int
    result_id: int
    manual_status: str
    manual_remark: Optional[str]
    reviewer: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PromptTestRunDetailResponse(BaseModel):
    run: PromptTestRunRead
    result: PromptTestResultRead
    results: Optional[list[PromptRepeatResultItem]] = None
    assertion: Optional[PromptAssertionRead] = None
    input_snapshot: Optional[PromptInputSnapshotRead] = None
    latest_score: Optional[PromptScoreRead] = None
    latest_manual_review: Optional[PromptManualReviewRead] = None


class PromptRunInfoSummary(BaseModel):
    id: int
    status: str
    prompt_version_id: int
    model_config_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]


class PromptVersionSummary(BaseModel):
    id: int
    prompt_name: str
    version: str
    is_baseline: bool
    baseline_version_id: Optional[int]
    status: str


class ModelConfigSummary(BaseModel):
    id: int
    config_name: str
    provider: str
    base_url: Optional[str]
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    is_default: bool
    status: str


class PromptResultSummary(BaseModel):
    total: int
    success_count: int
    failed_count: int
    assertion_passed_count: int
    assertion_failed_count: int
    assertion_skipped_count: int
    success_rate: float
    assertion_pass_rate: float


class PromptManualCheckSuggestion(BaseModel):
    need_manual_check: bool
    reasons: list[str]


class PromptFailureSummaryItem(BaseModel):
    result_id: int
    repeat_index: int
    status: str
    assertion_status: Optional[str]
    reason_summary: str
    actual_output_summary: str


class PromptTestRunSummaryResponse(BaseModel):
    # Pydantic v2 中 `model_config` 是保留配置名，不能作为业务字段名使用。
    model_config = ConfigDict(populate_by_name=True)

    run_id: int
    status: str
    prompt_version_id: int
    model_config_id: int
    run_info: PromptRunInfoSummary
    prompt_version: Optional[PromptVersionSummary] = None
    # 内部字段使用 `model_config_info`，对外仍通过 alias 输出为 `model_config`。
    # 构造响应时请使用 `model_config_info=...`，不要使用 `model_config=...`。
    model_config_info: Optional[ModelConfigSummary] = Field(None, alias="model_config")
    input_snapshot: Optional[PromptInputSnapshotRead] = None
    result_summary: PromptResultSummary
    latest_score: Optional[PromptScoreRead] = None
    latest_manual_review: Optional[PromptManualReviewRead] = None
    manual_check_suggestion: PromptManualCheckSuggestion
    failure_summary: list[PromptFailureSummaryItem]


class PromptRunComparison(BaseModel):
    success_rate_diff: float
    assertion_pass_rate_diff: float
    total_score_diff: Optional[float]
    result: str
    reasons: list[str]


class PromptRunCompareResponse(BaseModel):
    current_run_id: int
    baseline_run_id: int
    current_summary: PromptTestRunSummaryResponse
    baseline_summary: PromptTestRunSummaryResponse
    comparison: PromptRunComparison
    manual_check_suggestion: PromptManualCheckSuggestion
    baseline_relation_matched: Optional[bool]


def parse_csv_cases(content: str) -> list[ParsedCsvCase]:
    reader = csv.DictReader(io.StringIO(content))
    expected_fields = ["case_id", "case_name", "input_text", "assert_type", "expected_value"]
    if reader.fieldnames != expected_fields:
        raise ValueError(f"CSV header must be exactly: {','.join(expected_fields)}")

    parsed: list[ParsedCsvCase] = []
    for idx, row in enumerate(reader, start=2):
        try:
            parsed.append(ParsedCsvCase(**row))
        except Exception as exc:
            raise ValueError(f"Invalid CSV row at line {idx}: {exc}") from exc

    if not parsed:
        raise ValueError("CSV must contain at least one test case")
    return parsed


def validate_assert_regex(pattern: str) -> None:
    re.compile(pattern)
