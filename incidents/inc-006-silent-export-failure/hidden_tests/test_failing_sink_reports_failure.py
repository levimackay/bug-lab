from export.job import ExportJob


class FailingSink:
    """Simulates a downstream sink that is unavailable (a dead partner
    endpoint, an unmounted share, whatever this week's outage is)."""

    def write(self, records) -> None:
        raise ConnectionError("partner endpoint unreachable")


def test_job_reports_failure_when_sink_write_fails():
    result = ExportJob(FailingSink()).run()
    assert result.success is False


def test_job_does_not_claim_rows_were_exported_on_failure():
    result = ExportJob(FailingSink()).run()
    assert result.rows_exported == 0


def test_failure_result_carries_the_error():
    result = ExportJob(FailingSink()).run()
    assert "partner endpoint unreachable" in result.error
