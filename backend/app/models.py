from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class TestTarget(Base):
    __tablename__ = "test_targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    target_type = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    endpoint_url = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    headers_json = Column(Text, nullable=True)
    body_template = Column(Text, nullable=True)
    prompt_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TestSuite(Base):
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    case_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cases = relationship("TestCase", back_populates="suite", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False, index=True)
    case_id = Column(String(50), nullable=False)
    case_name = Column(String(200), nullable=False)
    input_text = Column(Text, nullable=False)
    assert_type = Column(String(20), nullable=False)
    expected_value = Column(Text, nullable=False)

    suite = relationship("TestSuite", back_populates="cases")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("test_targets.id"), nullable=False)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    status = Column(String(20), nullable=False)
    total = Column(Integer, default=0, nullable=False)
    passed = Column(Integer, default=0, nullable=False)
    failed = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False, index=True)
    case_id = Column(String(50), nullable=False)
    case_name = Column(String(200), nullable=False)
    input_text = Column(Text, nullable=False)
    actual_output = Column(Text, nullable=False)
    assert_type = Column(String(20), nullable=False)
    expected_value = Column(Text, nullable=False)
    passed = Column(Boolean, nullable=False)
    reason = Column(Text, nullable=False)
    latency_ms = Column(Integer, nullable=False)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_name = Column(String(200), nullable=False)
    version = Column(String(50), nullable=False)
    prompt_content = Column(Text, nullable=False)
    is_baseline = Column(Boolean, default=False, nullable=False)
    baseline_version_id = Column(Integer, nullable=True)
    status = Column(String(20), default="draft", nullable=False)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(200), nullable=False)
    provider = Column(String(50), nullable=False)
    base_url = Column(String(500), nullable=True)
    model = Column(String(100), nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    top_p = Column(Float, default=1.0, nullable=False)
    max_tokens = Column(Integer, default=2048, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PromptTestRun(Base):
    __tablename__ = "prompt_test_runs"

    id = Column(Integer, primary_key=True, index=True)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=False, index=True)
    model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=False, index=True)
    input_text = Column(Text, nullable=False)
    prompt_content_snapshot = Column(Text, nullable=False)
    model_config_snapshot = Column(Text, nullable=False)
    repeat_count = Column(Integer, default=1, nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)


class PromptTestResult(Base):
    __tablename__ = "prompt_test_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("prompt_test_runs.id"), nullable=False, index=True)
    repeat_index = Column(Integer, default=1, nullable=False)
    actual_output = Column(Text, nullable=False)
    raw_response = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PromptTestAssertionResult(Base):
    __tablename__ = "prompt_test_assertion_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("prompt_test_runs.id"), nullable=False, index=True)
    result_id = Column(Integer, ForeignKey("prompt_test_results.id"), nullable=False, index=True)
    assert_type = Column(String(20), nullable=True)
    expected_value = Column(Text, nullable=True)
    assertion_status = Column(String(20), nullable=False)
    assertion_passed = Column(Boolean, nullable=True)
    assertion_reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PromptTestInputSnapshot(Base):
    __tablename__ = "prompt_test_input_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("prompt_test_runs.id"), nullable=False, index=True)
    input_text = Column(Text, nullable=True)
    input_variables_json = Column(Text, nullable=True)
    rendered_prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PromptScoreResult(Base):
    __tablename__ = "prompt_score_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("prompt_test_runs.id"), nullable=False, index=True)
    result_id = Column(Integer, ForeignKey("prompt_test_results.id"), nullable=False, index=True)
    scorer_model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=False)
    scoring_template_id = Column(String(100), nullable=False)
    expected_behavior = Column(Text, nullable=True)
    dimension_scores_json = Column(Text, nullable=True)
    total_score = Column(Float, nullable=True)
    score_reason = Column(Text, nullable=True)
    problem_points_json = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=False)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PromptManualReview(Base):
    __tablename__ = "prompt_manual_reviews"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("prompt_test_runs.id"), nullable=False, index=True)
    result_id = Column(Integer, ForeignKey("prompt_test_results.id"), nullable=False, index=True)
    manual_status = Column(String(20), nullable=False)
    manual_remark = Column(Text, nullable=True)
    reviewer = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
